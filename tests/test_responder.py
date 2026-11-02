import socket
import threading
import unittest

from pjs.responder import MikroTikResponder, RouterOSClient, encode_length, encode_sentence


def read_sentence(sock):
    """Pembaca sederhana untuk router palsu (panjang kata < 128 sudah cukup di sini)."""
    words = []
    while True:
        n = sock.recv(1)[0]
        if n == 0:
            return words
        data = b""
        while len(data) < n:
            data += sock.recv(n - len(data))
        words.append(data.decode())


class FakeRouter(threading.Thread):
    """Router MikroTik palsu: menerima login, add, print, remove."""

    def __init__(self):
        super().__init__(daemon=True)
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.received = []
        self.entries = {}

    def run(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            with conn:
                while True:
                    try:
                        words = read_sentence(conn)
                    except (IndexError, OSError):
                        break
                    self.received.append(words)
                    conn.sendall(self.reply(words))

    def reply(self, words):
        cmd = words[0]
        attrs = dict(w[1:].split("=", 1) for w in words[1:] if w.startswith("="))
        if cmd == "/login":
            ok = attrs.get("password") == "rahasia"
            return encode_sentence(["!done"]) if ok else encode_sentence(["!trap", "=message=invalid user name or password"]) + encode_sentence(["!done"])
        if cmd.endswith("/add"):
            if attrs["address"] in self.entries.values():
                return encode_sentence(["!trap", "=message=failure: already have such entry"]) + encode_sentence(["!done"])
            self.entries["*1"] = attrs["address"]
            return encode_sentence(["!done", "=ret=*1"])
        if cmd.endswith("/print"):
            wanted = next(w[9:] for w in words if w.startswith("?address="))
            rows = [encode_sentence(["!re", f"=.id={i}"]) for i, a in self.entries.items() if a == wanted]
            return b"".join(rows) + encode_sentence(["!done"])
        if cmd.endswith("/remove"):
            self.entries.pop(attrs[".id"], None)
            return encode_sentence(["!done"])
        return encode_sentence(["!done"])


class EncodingTest(unittest.TestCase):
    def test_lengths(self):
        self.assertEqual(encode_length(0x7F), b"\x7f")
        self.assertEqual(encode_length(0x80), b"\x80\x80")
        self.assertEqual(encode_length(0x3FFF), b"\xbf\xff")
        self.assertEqual(encode_length(0x4000), b"\xc0\x40\x00")
        self.assertEqual(encode_length(0x200000), b"\xe0\x20\x00\x00")

    def test_long_word_roundtrip(self):
        router = socket.socketpair()
        client = RouterOSClient("x")
        client.sock = router[0]
        word = "=comment=" + "a" * 300
        router[1].sendall(encode_sentence(["!re", word]))
        self.assertEqual(client._read_sentence(), ["!re", word])
        router[0].close()
        router[1].close()


class ResponderTest(unittest.TestCase):
    def setUp(self):
        self.router = FakeRouter()
        self.router.start()
        self.cfg = {"enabled": True, "host": "127.0.0.1", "port": self.router.port, "user": "pjs",
                    "password": "rahasia", "address_list": "pjs-karantina", "timeout": "24h"}

    def tearDown(self):
        self.router.server.close()

    def test_isolate_and_release(self):
        responder = MikroTikResponder(self.cfg)
        ok, message = responder.isolate("10.10.0.66", "PJS-0001 otomatis")
        self.assertTrue(ok, message)
        self.assertEqual(self.router.entries, {"*1": "10.10.0.66"})
        add = next(w for w in self.router.received if w[0].endswith("/add"))
        self.assertIn("=list=pjs-karantina", add)
        self.assertIn("=timeout=24h", add)
        ok, message = responder.isolate("10.10.0.66", "lagi")
        self.assertTrue(ok, message)
        ok, message = responder.release("10.10.0.66")
        self.assertTrue(ok, message)
        self.assertEqual(self.router.entries, {})

    def test_wrong_password(self):
        responder = MikroTikResponder({**self.cfg, "password": "salah"})
        ok, message = responder.isolate("10.10.0.66", "x")
        self.assertFalse(ok)
        self.assertIn("invalid", message)

    def test_test_mode_sends_nothing(self):
        responder = MikroTikResponder({**self.cfg, "enabled": False})
        ok, _ = responder.isolate("10.10.0.66", "x")
        self.assertTrue(ok)
        self.assertEqual(responder.mode, "uji")
        self.assertEqual(self.router.received, [])


if __name__ == "__main__":
    unittest.main()
