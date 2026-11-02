import json
import os
import tempfile
import unittest
from pathlib import Path

from pjs import ed25519_pure
from pjs.evidence import EvidenceLog, Signer


class Ed25519Test(unittest.TestCase):
    def test_rfc8032_vector_1(self):
        secret = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        public = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        signature = bytes.fromhex(
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065"
            "224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
        )
        self.assertEqual(ed25519_pure.public_key(secret), public)
        self.assertEqual(ed25519_pure.sign(secret, b""), signature)
        self.assertTrue(ed25519_pure.verify(public, b"", signature))
        self.assertFalse(ed25519_pure.verify(public, b"x", signature))

    def test_pure_matches_library(self):
        seed = os.urandom(32)
        message = b"pos jaga siber"
        signer = Signer(seed)
        self.assertEqual(ed25519_pure.public_key(seed), signer.public)
        self.assertEqual(ed25519_pure.sign(seed, message), signer.sign(message))


class EvidenceLogTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.path = base / "bukti.jsonl"
        self.key = base / "kunci.key"
        self.log = EvidenceLog(self.path, self.key)
        for n in range(5):
            self.log.append("uji", {"n": n})

    def tearDown(self):
        self.dir.cleanup()

    def _lines(self):
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines()]

    def _write(self, entries):
        self.path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")

    def test_intact_chain(self):
        result = self.log.verify()
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 5)

    def test_changed_entry_is_detected(self):
        entries = self._lines()
        entries[2]["data"]["n"] = 99
        self._write(entries)
        result = self.log.verify()
        self.assertFalse(result["ok"])
        self.assertEqual(result["broken_at"], 3)
        self.assertIn("diubah", result["message"])

    def test_deleted_entry_is_detected(self):
        entries = self._lines()
        del entries[1]
        self._write(entries)
        result = self.log.verify()
        self.assertFalse(result["ok"])
        self.assertEqual(result["broken_at"], 2)
        self.assertIn("hilang", result["message"])

    def test_rewritten_hash_without_key_fails_signature(self):
        from pjs.evidence import entry_hash

        entries = self._lines()
        entries[4]["data"]["n"] = 42
        entries[4]["hash"] = entry_hash(entries[4])
        self._write(entries)
        result = self.log.verify()
        self.assertFalse(result["ok"])
        self.assertIn("Tanda tangan", result["message"])

    def test_book_code_and_lookup(self):
        code = self.log.code()
        self.assertRegex(code, r"^[0-9A-F]{4}-[0-9A-F]{4}$")
        self.assertEqual(self.log.find_code(code), 5)
        self.assertIsNone(self.log.find_code("0000-0000"))

    def test_continues_after_restart(self):
        reopened = EvidenceLog(self.path, self.key)
        reopened.append("uji", {"n": 5})
        self.assertTrue(reopened.verify()["ok"])
        self.assertEqual(reopened.count, 6)


if __name__ == "__main__":
    unittest.main()
