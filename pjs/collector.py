"""Membaca eve.json milik Suricata baris demi baris, seperti `tail -f`.

Suricata menulis satu kejadian per baris (JSON Lines). Pembaca ini:
- menunggu kalau berkas belum ada,
- mulai dari akhir berkas (kecuali diminta dari awal),
- membuka ulang kalau berkas diputar (logrotate) atau dikosongkan.
"""

import json
import logging
import os
import threading
import time

log = logging.getLogger("pjs.collector")


class EveTailer(threading.Thread):
    def __init__(self, path, handler, from_start=False, poll_s=0.5):
        super().__init__(name="pembaca-eve", daemon=True)
        self.path, self.handler = str(path), handler
        self.from_start, self.poll_s = from_start, poll_s
        self._stop_event = threading.Event()
        self.lines_read = 0

    def stop(self):
        self._stop_event.set()

    def _open(self, seek_end):
        f = open(self.path, "rb")
        if seek_end:
            f.seek(0, os.SEEK_END)
        return f

    def run(self):
        existed_at_start = os.path.exists(self.path)
        f, buf = None, b""
        while not self._stop_event.is_set():
            if f is None:
                if not os.path.exists(self.path):
                    time.sleep(self.poll_s)
                    continue
                # Berkas yang sudah ada saat kotak menyala: lompat ke akhir.
                # Berkas baru (muncul belakangan atau hasil rotasi): baca dari awal.
                f = self._open(seek_end=existed_at_start and not self.from_start)
                existed_at_start = False
            chunk = f.readline()
            if chunk:
                buf += chunk
                if buf.endswith(b"\n"):
                    self._handle(buf)
                    buf = b""
                continue
            time.sleep(self.poll_s)
            if self._rotated(f):
                f.close()
                f, buf = None, b""

    def _rotated(self, f):
        try:
            on_disk = os.stat(self.path)
        except FileNotFoundError:
            return True
        current = os.fstat(f.fileno())
        if on_disk.st_size < f.tell():
            return True
        return bool(on_disk.st_ino and current.st_ino and on_disk.st_ino != current.st_ino)

    def _handle(self, raw):
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            return
        try:
            event = json.loads(line)
        except ValueError:
            log.warning("Baris eve.json tidak bisa dibaca, dilewati.")
            return
        self.lines_read += 1
        try:
            self.handler(event)
        except Exception:
            log.exception("Gagal memproses satu kejadian, kotak tetap berjalan.")
