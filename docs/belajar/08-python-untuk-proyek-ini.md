# 08 · Python untuk proyek ini

Bab ini **bukan** kursus Python lengkap. Isinya hanya bagian Python yang benar-benar dipakai di repositori, dengan contoh dari kode proyek. Kalau belum pernah memakai Python sama sekali, pelajari dulu dasar variabel, `if`, `for`, dan fungsi (cukup 1–2 jam dari tutorial mana pun).

Proyek ini sengaja **hanya memakai pustaka bawaan Python**. Tidak perlu `pip install` untuk menjalankan kotak, sehingga mudah dipasang di markas tanpa internet.

## 1. Paket dan modul

```
pjs/
  __init__.py      ← menandai folder ini sebagai paket Python
  __main__.py      ← dijalankan saat mengetik: python -m pjs
  config.py        ← modul; diimpor dengan: from pjs import config
  ...
```

Di dalam paket, modul saling mengimpor dengan titik (impor relatif):

```python
from . import playbook             # modul lain di folder yang sama
from .store import Store           # satu kelas dari modul store
```

`python -m pjs demo` artinya: "jalankan paket `pjs` sebagai program, dengan argumen `demo`".

## 2. Dict, list, dan f-string

Hampir semua data di kotak berbentuk **dict** (pasangan kunci-nilai), karena cocok dengan JSON:

```python
incident = {"id": "PJS-0002", "severity": "kritis", "count": 3}
incident["count"] += 1
print(f"{incident['id']} terjadi {incident['count']} kali")
```

`dict.get(kunci, bawaan)` mengambil nilai tanpa galat kalau kuncinya tidak ada. Ini sering dipakai karena catatan Suricata tidak selalu lengkap:

```python
alert = event.get("alert") or {}
meta = alert.get("metadata") or {}
```

## 3. Kelas

Kelas mengelompokkan data dan fungsi yang berhubungan. Contoh ringkas dari `pjs/responder.py`:

```python
class MikroTikResponder:
    def __init__(self, cfg):              # dijalankan saat objek dibuat
        self.enabled = bool(cfg.get("enabled"))

    @property
    def mode(self):                       # dipanggil tanpa kurung: responder.mode
        return "mikrotik" if self.enabled else "uji"

    def isolate(self, ip, comment):       # metode biasa
        ...

responder = MikroTikResponder({"enabled": False})
print(responder.mode)                      # "uji"
```

Tes memakai kelas palsu (`FakeResponder` di `tests/test_detector.py`) yang punya metode sama. Detektor tidak peduli apakah yang dipanggil MikroTik sungguhan atau palsu, selama metodenya ada. Cara ini membuat kode mudah diuji.

## 4. `with`, galat, dan `try`

`with` memastikan sesuatu ditutup walaupun terjadi galat:

```python
with open(path, "a", encoding="utf-8") as f:
    f.write(line)
# berkas pasti tertutup di sini
```

`try/except` menangkap galat supaya kotak tidak berhenti:

```python
try:
    self.handler(event)
except Exception:
    log.exception("Gagal memproses satu kejadian, kotak tetap berjalan.")
```

Prinsip di kotak: **satu catatan rusak tidak boleh menghentikan penjagaan.**

## 5. JSON dan berkas

```python
import json
event = json.loads('{"src_ip": "10.10.0.66"}')    # teks → dict
text = json.dumps(event, ensure_ascii=False)      # dict → teks (huruf non-Inggris tetap utuh)
```

`pathlib.Path` dipakai untuk jalur berkas karena bekerja sama di Windows dan Linux:

```python
from pathlib import Path
data_dir = Path("data-demo")
log_path = data_dir / "bukti.jsonl"              # data-demo/bukti.jsonl
```

## 6. Byte, heksadesimal, dan `struct`

Protokol jaringan bekerja dengan **byte**, bukan teks. Python memakai tipe `bytes`:

```python
data = bytes([0x00, 0x01, 0x05])
print(data.hex(" "))           # "00 01 05"
bytes.fromhex("ff00")          # b'\xff\x00'
```

`struct` mengubah angka menjadi byte dengan format tertentu, dan sebaliknya. Dipakai di genset tiruan dan skrip serangan:

```python
import struct
struct.pack(">HB", 6, 1)              # b'\x00\x06\x01'  (H = 2 byte, B = 1 byte, > = big-endian)
struct.unpack(">HH", b"\x00\x00\xff\x00")   # (0, 65280)
```

## 7. Socket

**Socket** adalah "colokan" program ke jaringan. Contoh klien TCP dari `lab/serangan_genset.py`:

```python
import socket
with socket.create_connection(("127.0.0.1", 5020), timeout=3) as sock:
    sock.sendall(request)        # kirim semua byte
    reply = sock.recv(256)       # terima paling banyak 256 byte
```

`recv` bisa mengembalikan data **lebih sedikit** dari yang diminta. Karena itu ada fungsi `_recv_exact` yang mengulang sampai jumlah byte terpenuhi (di `responder.py` dan `genset_tiruan.py`).

## 8. Thread, kunci, dan antrean

Kotak mengerjakan beberapa hal **bersamaan**: membaca `eve.json`, melayani dashboard, menunggu AI, dan memeriksa rantai. Masing-masing berjalan di **thread** sendiri:

| Thread | Tugas | Berkas |
|---|---|---|
| `pembaca-eve` | Membaca eve.json terus-menerus | `collector.py` |
| `penjelas-ai` | Mengirim prompt ke Ollama satu per satu | `explainer.py` |
| `pemeriksa-rantai` | Memeriksa catatan bukti setiap 5 menit | `app.py` |
| thread server web | Satu thread per permintaan dashboard | `server.py` |

Kalau dua thread mengubah data yang sama bersamaan, hasilnya bisa kacau. **Kunci** (`threading.Lock`) memastikan hanya satu thread yang masuk:

```python
with self._lock:
    ...   # hanya satu thread boleh di sini pada satu waktu
```

`queue.Queue` adalah antrean aman antar-thread. Detektor memasukkan permintaan penjelasan, thread AI mengambilnya satu per satu.

## 9. SQLite

SQLite adalah database dalam **satu berkas** (`pjs.sqlite3`), sudah bawaan Python. Dipakai untuk perangkat, kejadian, dan penekanan alarm:

```python
import sqlite3
db = sqlite3.connect("pjs.sqlite3")
db.execute("SELECT * FROM incidents WHERE status = ?", ("menunggu",))
```

Tanda `?` diisi nilai secara aman. **Jangan pernah** menyusun SQL dengan menempel teks dari luar, misalnya `f"... WHERE id = '{masukan}'"`, karena itu membuka celah **SQL injection**.

## 10. Server web, argumen, catatan, dan tes

| Pustaka | Dipakai untuk | Berkas |
|---|---|---|
| `http.server` | Server dashboard dan API | `server.py` |
| `urllib.request` | Mengirim permintaan ke Ollama | `explainer.py` |
| `argparse` | Membaca perintah `python -m pjs ...` | `__main__.py` |
| `logging` | Menulis pesan ke layar dengan waktu dan sumbernya | semua |
| `unittest` | Tes otomatis | `tests/` |
| `hashlib` | SHA-256 | `evidence.py` |
| `ipaddress` | Memeriksa alamat dan jaringan | `config.py` |

Menjalankan tes:

```bash
python -m unittest discover -s tests -t .          # semua tes
python -m unittest tests.test_evidence -v           # satu berkas, dengan rincian
```

## Latihan

1. Di Python interaktif, buat dict kejadian, tambahkan `count`, lalu ubah menjadi JSON.
2. Pakai `struct.pack` untuk membuat perintah Modbus **baca coil 0** (kode fungsi 1, jumlah 1). Kirim ke genset tiruan dan baca balasannya.
3. Buka `pjs/store.py`. Temukan semua tempat yang memakai `?` di SQL. Adakah yang menempel teks langsung?
4. Tambahkan satu tes kecil di `tests/test_detector.py` yang memeriksa bahwa kejadian kamera berstatus `menunggu`. Jalankan semua tes.

## Kamu paham kalau...

- bisa menjalankan tes dan membaca hasilnya,
- tahu kenapa kotak memakai beberapa thread dan apa gunanya kunci,
- bisa membaca `responder.py` atau `genset_tiruan.py` tanpa bingung soal byte dan socket.
