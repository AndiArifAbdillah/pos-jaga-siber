"""Mengisolasi perangkat lewat API MikroTik RouterOS.

Caranya: alamat perangkat dimasukkan ke daftar alamat (address-list)
"pjs-karantina" dengan batas waktu (bawaan 24 jam). Di router sudah ada aturan
firewall yang membuang semua lalu lintas dari dan ke daftar itu. Setelah batas
waktu habis, router menghapus alamat itu sendiri, jadi salah blokir tidak
berlangsung selamanya.

Protokol API RouterOS (port 8728):
- Pesan disebut "kalimat", isinya beberapa "kata", diakhiri kata kosong.
- Setiap kata diawali panjangnya (1 sampai 5 byte), lalu isinya.
- Balasan diawali "!re" (baris data), "!done" (selesai), "!trap" (galat), atau "!fatal".
"""

import hashlib
import socket


class RouterOSError(Exception):
    pass


def encode_length(n):
    if n < 0x80:
        return bytes([n])
    if n < 0x4000:
        return (n | 0x8000).to_bytes(2, "big")
    if n < 0x200000:
        return (n | 0xC00000).to_bytes(3, "big")
    if n < 0x10000000:
        return (n | 0xE0000000).to_bytes(4, "big")
    return b"\xf0" + n.to_bytes(4, "big")


def encode_word(word):
    data = word.encode("utf-8")
    return encode_length(len(data)) + data


def encode_sentence(words):
    return b"".join(encode_word(w) for w in words) + b"\x00"


class RouterOSClient:
    def __init__(self, host, port=8728, timeout=5.0):
        self.host, self.port, self.timeout = host, port, timeout
        self.sock = None

    def __enter__(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        return self

    def __exit__(self, *exc):
        if self.sock:
            self.sock.close()
            self.sock = None

    def _recv_exact(self, n):
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise RouterOSError("Sambungan ke router terputus.")
            data += chunk
        return data

    def _read_length(self):
        first = self._recv_exact(1)[0]
        if first < 0x80:
            return first
        if first < 0xC0:
            return int.from_bytes(bytes([first & 0x3F]) + self._recv_exact(1), "big")
        if first < 0xE0:
            return int.from_bytes(bytes([first & 0x1F]) + self._recv_exact(2), "big")
        if first < 0xF0:
            return int.from_bytes(bytes([first & 0x0F]) + self._recv_exact(3), "big")
        return int.from_bytes(self._recv_exact(4), "big")

    def _read_sentence(self):
        words = []
        while True:
            length = self._read_length()
            if length == 0:
                return words
            words.append(self._recv_exact(length).decode("utf-8", errors="replace"))

    def talk(self, words):
        """Kirim satu perintah. Hasilnya daftar baris data (dict). Galat menjadi RouterOSError."""
        self.sock.sendall(encode_sentence(words))
        rows, error = [], None
        while True:
            sentence = self._read_sentence()
            if not sentence:
                continue
            kind, attrs = sentence[0], {}
            for word in sentence[1:]:
                if word.startswith("="):
                    key, _, value = word[1:].partition("=")
                    attrs[key] = value
            if kind == "!re":
                rows.append(attrs)
            elif kind == "!trap":
                error = attrs.get("message", "galat tanpa pesan")
            elif kind == "!fatal":
                raise RouterOSError(attrs.get("message", " ".join(sentence[1:])))
            elif kind == "!done":
                if error:
                    raise RouterOSError(error)
                # RouterOS lama (sebelum 6.43) membalas login dengan tantangan "ret".
                if attrs.get("ret") and not rows:
                    rows.append(attrs)
                return rows

    def login(self, user, password):
        rows = self.talk(["/login", f"=name={user}", f"=password={password}"])
        if rows and "ret" in rows[0]:
            challenge = bytes.fromhex(rows[0]["ret"])
            digest = hashlib.md5(b"\x00" + password.encode("utf-8") + challenge).hexdigest()
            self.talk(["/login", f"=name={user}", f"=response=00{digest}"])


class MikroTikResponder:
    """Kalau `enabled` mati, kotak berjalan dalam mode uji: perintah hanya dicatat."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled"))
        self.list_name = cfg.get("address_list", "pjs-karantina")
        self.timeout = cfg.get("timeout", "24h")

    @property
    def mode(self):
        return "mikrotik" if self.enabled else "uji"

    def _client(self):
        client = RouterOSClient(self.cfg["host"], int(self.cfg.get("port", 8728)))
        client.__enter__()
        try:
            client.login(self.cfg["user"], self.cfg.get("password", ""))
        except Exception:
            client.__exit__()
            raise
        return client

    def isolate(self, ip, comment):
        """Hasil: (berhasil, pesan)."""
        if not self.enabled:
            return True, "Mode uji: perintah blokir tidak dikirim ke MikroTik."
        try:
            client = self._client()
            try:
                client.talk([
                    "/ip/firewall/address-list/add",
                    f"=list={self.list_name}",
                    f"=address={ip}",
                    f"=timeout={self.timeout}",
                    f"=comment={comment}",
                ])
            finally:
                client.__exit__()
        except RouterOSError as exc:
            if "already have" in str(exc):
                return True, f"{ip} sudah ada di daftar {self.list_name}."
            return False, f"MikroTik menolak: {exc}"
        except OSError as exc:
            return False, f"MikroTik tidak bisa dihubungi: {exc}"
        return True, f"{ip} masuk daftar {self.list_name} selama {self.timeout}."

    def release(self, ip):
        if not self.enabled:
            return True, "Mode uji: perintah lepas tidak dikirim ke MikroTik."
        try:
            client = self._client()
            try:
                rows = client.talk([
                    "/ip/firewall/address-list/print",
                    "=.proplist=.id",
                    f"?list={self.list_name}",
                    f"?address={ip}",
                ])
                for row in rows:
                    client.talk(["/ip/firewall/address-list/remove", f"=.id={row['.id']}"])
            finally:
                client.__exit__()
        except (RouterOSError, OSError) as exc:
            return False, f"Gagal melepas di MikroTik: {exc}"
        return True, f"{ip} dikeluarkan dari daftar {self.list_name}."

    def check(self):
        """Dipakai perintah `python -m pjs uji-mikrotik`."""
        client = self._client()
        try:
            identity = client.talk(["/system/identity/print"])
            entries = client.talk(["/ip/firewall/address-list/print", f"?list={self.list_name}"])
        finally:
            client.__exit__()
        name = identity[0].get("name", "?") if identity else "?"
        return name, entries
