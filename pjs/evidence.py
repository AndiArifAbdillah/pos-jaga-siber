"""Catatan bukti anti-ubah (rantai hash + tanda tangan Ed25519).

Setiap entri menyimpan sidik jari (hash SHA-256) entri sebelumnya. Kalau satu
entri diubah atau dihapus, sambungan rantai setelahnya putus dan `verify()`
menunjukkan di mana. Setiap entri juga ditandatangani kunci milik kotak.

Bentuk satu baris di berkas (JSON Lines):
  {"seq": 12, "time": "...", "kind": "kejadian_baru", "data": {...},
   "prev": "<hash entri 11>", "hash": "<hash entri ini>", "sig": "<tanda tangan>"}
"""

import hashlib
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from . import ed25519_pure

GENESIS = "0" * 64


def canonical(obj):
    """JSON dengan urutan kunci tetap, supaya hash selalu sama untuk isi yang sama."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def entry_hash(entry):
    body = {k: entry[k] for k in ("seq", "time", "kind", "data", "prev")}
    return hashlib.sha256(canonical(body)).hexdigest()


def format_code(hash_hex):
    """Kode buku jaga: 8 huruf pertama hash, misalnya 'A1B2-C3D4'."""
    head = hash_hex[:8].upper()
    return f"{head[:4]}-{head[4:]}"


class Signer:
    """Kunci tanda tangan kotak. Memakai `cryptography` kalau ada, kalau tidak Python murni."""

    def __init__(self, seed):
        self.seed = seed
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

            self._key = Ed25519PrivateKey.from_private_bytes(seed)
            self.public = self._key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            self.backend = "cryptography"
        except ImportError:
            self._key = None
            self.public = ed25519_pure.public_key(seed)
            self.backend = "python-murni"

    def sign(self, message):
        if self._key is not None:
            return self._key.sign(message)
        return ed25519_pure.sign(self.seed, message)

    @staticmethod
    def verify(public, message, signature):
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except ImportError:
            return ed25519_pure.verify(public, message, signature)
        try:
            Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
            return True
        except (InvalidSignature, ValueError):
            return False

    @classmethod
    def load_or_create(cls, key_path):
        key_path = Path(key_path)
        if key_path.exists():
            seed = bytes.fromhex(key_path.read_text(encoding="ascii").strip())
        else:
            key_path.parent.mkdir(parents=True, exist_ok=True)
            seed = os.urandom(32)
            key_path.write_text(seed.hex() + "\n", encoding="ascii")
            try:
                os.chmod(key_path, 0o600)
            except OSError:
                pass
        signer = cls(seed)
        pub_path = key_path.with_suffix(".pub")
        if not pub_path.exists():
            pub_path.write_text(signer.public.hex() + "\n", encoding="ascii")
        return signer


class EvidenceLog:
    def __init__(self, path, key_path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.signer = Signer.load_or_create(key_path)
        self._lock = threading.Lock()
        self._seq, self._head = self._read_tail()

    def _read_tail(self):
        """Ambil nomor dan hash entri terakhir yang masih bisa dibaca."""
        if not self.path.exists():
            return 0, GENESIS
        for line in reversed(self.path.read_text(encoding="utf-8").splitlines()):
            try:
                entry = json.loads(line)
                return int(entry["seq"]), entry["hash"]
            except (ValueError, KeyError, TypeError):
                continue
        return 0, GENESIS

    def append(self, kind, data):
        with self._lock:
            entry = {
                "seq": self._seq + 1,
                "time": datetime.now().astimezone().isoformat(timespec="seconds"),
                "kind": kind,
                "data": data,
                "prev": self._head,
            }
            entry["hash"] = entry_hash(entry)
            entry["sig"] = self.signer.sign(bytes.fromhex(entry["hash"])).hex()
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self._seq, self._head = entry["seq"], entry["hash"]
            return entry

    def entries(self):
        """Semua entri yang bisa dibaca (baris rusak dilewati)."""
        if not self.path.exists():
            return []
        result = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                result.append(json.loads(line))
            except ValueError:
                continue
        return result

    def tail(self, n):
        return self.entries()[-n:]

    @property
    def count(self):
        return self._seq

    def code(self):
        return format_code(self._head)

    def find_code(self, code):
        """Cari entri yang hash-nya diawali kode buku jaga. Hasilnya nomor entri atau None."""
        wanted = code.replace("-", "").strip().lower()
        if len(wanted) != 8:
            return None
        for entry in self.entries():
            if str(entry.get("hash", "")).startswith(wanted):
                return entry.get("seq")
        return None

    def verify(self, public=None):
        """Periksa seluruh rantai. Hasil: ok, jumlah entri, letak putus, dan pesan."""
        public = public or self.signer.public
        result = {"ok": True, "count": 0, "broken_at": None, "message": "Rantai utuh.", "checked_at": time.time()}

        def broken(seq, message):
            result.update(ok=False, broken_at=seq, message=message)
            return result

        if not self.path.exists():
            result["message"] = "Belum ada catatan."
            return result
        prev_hash, expected = GENESIS, 1
        lines = self.path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                seq = int(entry["seq"])
                stored_hash = entry["hash"]
            except (ValueError, KeyError, TypeError):
                return broken(expected, f"Baris ke-{line_no} rusak dan tidak bisa dibaca.")
            try:
                recomputed = entry_hash(entry)
            except KeyError:
                return broken(seq, f"Entri #{seq} tidak lengkap.")
            if recomputed != stored_hash:
                return broken(seq, f"Isi entri #{seq} sudah diubah.")
            if seq > expected:
                missing = f"#{expected}" if seq == expected + 1 else f"#{expected} sampai #{seq - 1}"
                return broken(expected, f"Entri {missing} hilang.")
            if seq < expected:
                return broken(seq, f"Urutan entri kacau di #{seq}.")
            if entry["prev"] != prev_hash:
                return broken(seq, f"Entri #{seq} tidak tersambung ke entri sebelumnya.")
            try:
                signature = bytes.fromhex(entry["sig"])
            except (KeyError, ValueError):
                return broken(seq, f"Tanda tangan entri #{seq} tidak ada.")
            if not Signer.verify(public, bytes.fromhex(stored_hash), signature):
                return broken(seq, f"Tanda tangan entri #{seq} tidak sah.")
            prev_hash, expected = stored_hash, seq + 1
            result["count"] = seq
        result["message"] = f"Rantai utuh: {result['count']} entri diperiksa." if result["count"] else "Belum ada catatan."
        return result
