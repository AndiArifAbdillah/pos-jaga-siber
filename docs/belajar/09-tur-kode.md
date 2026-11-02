# 09 · Tur kode: perjalanan satu serangan dari paket sampai layar

Bab ini mengikuti **satu serangan genset** dari detik pertama sampai muncul di dashboard, sambil menunjuk berkas dan fungsi yang bekerja di setiap langkah. Buka berkasnya di editor sambil membaca.

## 1. Peta berkas

| Berkas | Peran | Dipanggil oleh |
|---|---|---|
| `pjs/__main__.py` | Pintu masuk perintah `python -m pjs ...` | Kamu |
| `pjs/config.py` | Membaca konfigurasi, menjawab "alamat ini di jaringan mana?" | Hampir semua |
| `pjs/app.py` | Merakit semua bagian, menyusun data dashboard | `__main__` |
| `pjs/collector.py` | Membaca `eve.json` baris demi baris | `app` |
| `pjs/detector.py` | **Otak**: perangkat, aturan, kejadian, keputusan, tindakan | `collector`, `server` |
| `pjs/playbook.py` | Daftar jenis kejadian: judul, tingkat, penjelasan bawaan, langkah SOP | `detector`, `explainer` |
| `pjs/store.py` | Database SQLite | `detector`, `app` |
| `pjs/evidence.py` | Catatan bukti (rantai hash dan tanda tangan) | `detector`, `app` |
| `pjs/ed25519_pure.py` | Tanda tangan Ed25519 cadangan | `evidence` |
| `pjs/responder.py` | Blokir lewat API MikroTik | `detector` |
| `pjs/explainer.py` | Penjelasan bawaan dan AI | `detector` |
| `pjs/server.py` | Server web dan API | `__main__` |
| `pjs/replay.py` | Memutar contoh catatan untuk demo | `__main__` |
| `pjs/vendors.py` | Menebak merek dari MAC | `detector` |
| `web/*` | Dashboard (bab 10) | Browser |

```
__main__ ──► App ──┬── EveTailer (collector) ──► Detector.process
                   │                                 │
                   │                ┌────────────────┼──────────────┬───────────────┐
                   │                ▼                ▼              ▼               ▼
                   │              Store       EvidenceLog   MikroTikResponder   Explainer ──► Ollama
                   │
                   └── server (http) ──► App.status() / Detector.isolate() / ...
```

## 2. Saat kotak dinyalakan

`python -m pjs demo --putar --baru` menjalankan `main()` di `__main__.py`:

1. Membaca `config.demo.json` lewat `config.load()`. Nilai yang tidak diisi diambil dari `DEFAULTS`.
2. `--baru` menghapus folder `data-demo` (hanya folder itu, demi keamanan).
3. `cmd_run()` membuat `App(cfg)`. Di dalam `App.__init__`:
   - `Store` membuka atau membuat `data-demo/pjs.sqlite3`,
   - `EvidenceLog` membuka `bukti.jsonl` dan memuat kunci (membuat kunci baru kalau belum ada),
   - `MikroTikResponder` dan `Explainer` disiapkan,
   - `Detector` memuat perangkat dari konfigurasi ke database,
   - `EveTailer` disiapkan untuk membaca `data-demo/eve.json`.
4. `App.start()`: menyalakan AI, menulis entri **"kotak_menyala"** ke catatan bukti, lalu menjalankan thread pembaca dan pemeriksa rantai.
5. Server web mulai melayani di port 8080.
6. Karena ada `--putar`, thread `pemutar-contoh` mulai menulis isi `lab/contoh_eve.jsonl` ke `eve.json`.

## 3. Perjalanan satu serangan

### Langkah 1 · Paket lewat (detik 0,000)

Laptop asing `10.10.0.66` mengirim perintah Modbus "tulis coil 0 = mati" ke genset `10.20.0.10`. Paket melewati router. Salinannya sampai ke kotak.

### Langkah 2 · Suricata menulis peringatan (detik 0,01)

Suricata mencocokkan paket dengan aturan `sid:1990001` (bab 04) dan menulis satu baris `alert` ke `eve.json`. Dalam demo, langkah ini ditiru oleh `replay.py`.

### Langkah 3 · Kotak membaca baris baru (≤ 0,5 detik)

`EveTailer.run()` (`collector.py`) membaca berkas seperti `tail -f`. Setiap 0,5 detik ia memeriksa baris baru. Baris lengkap diubah menjadi dict dengan `json.loads`, lalu diserahkan ke `Detector.process(event)`.

### Langkah 4 · Mencatat perangkat

`Detector.process` mengambil waktu (`parse_ts`), lalu memanggil `_see_device` untuk alamat asal dan tujuan:

- `10.10.0.66` belum ada di database, masa belajar sudah selesai, dan alamat ini tidak ada di konfigurasi. Maka perangkat dicatat dengan sumber `baru`, dan `_raise("perangkat_baru", ...)` membuat kejadian **"Ada perangkat baru di jaringan"**.
- MAC di catatan ini milik router (`08:00:27:aa:00:02` ada di `router_macs`), jadi **tidak** ditempelkan ke laptop asing.

(Dalam contoh demo, laptop asing sudah terlihat lebih dulu lewat catatan `flow`, jadi kejadian perangkat baru muncul sebelum peringatan genset.)

### Langkah 5 · Menentukan jenis kejadian

Karena `event_type` bernilai `alert`, `_on_alert` dipanggil:

```python
kind, severity = _first(meta.get("pjs_jenis")), _first(meta.get("pjs_tingkat"))
# kind = "ot_tulis", severity = "kritis"
```

### Langkah 6 · Membuat kejadian

`_raise("ot_tulis", "kritis", "10.10.0.66", "10.20.0.10", facts, ts)`:

1. **Ditekan?** `store.is_suppressed(...)`. Kalau petugas pernah menekan "Bukan ancaman" untuk pasangan ini, berhenti di sini.
2. **Sudah ada yang terbuka?** `store.find_open_incident(...)`. Kalau ya, hanya `count` ditambah satu. Itulah kenapa tiga peringatan menjadi satu kejadian "Terjadi 3 kali".
3. **Kejadian baru.** Nomor dari `store.next_incident_id()` (`PJS-0002`). Judul dari `playbook` (`"Perintah asing ke {dst}"` → "Perintah asing ke Genset utama"). Penjelasan bawaan dan langkah SOP diisi lewat `explainer.template` dan `explainer.steps`.
4. Disimpan: `store.add_incident(...)`.
5. Dicatat: `evidence.append("kejadian_baru", {...})`.

### Langkah 7 · Memutuskan isolasi

```python
def _should_auto_isolate(self, severity, src, dst):
    if severity != "kritis" or not self.cfg["auto_isolate"]:
        return False
    if src in self.cfg.never_isolate:
        return False
    return "ot" in (self.cfg.zone_of(src), self.cfg.zone_of(dst))
```

Kritis, laptop asing tidak dilindungi, dan tujuannya jaringan peralatan. Maka `isolate(incident_id, by="otomatis")`:

1. `responder.isolate("10.10.0.66", comment="PJS-0002 otomatis")` mengirim perintah ke MikroTik (dalam demo: mode uji),
2. status menjadi `diisolasi`,
3. dicatat: `evidence.append("isolasi_otomatis", ...)`.

### Langkah 8 · Meminta penjelasan AI

`_ask_ai` menyusun prompt (`explainer.build_prompt`) dan memasukkannya ke antrean. Penjelasan ditandai `pending: True`, sehingga dashboard menulis "AI sedang menyusun penjelasan...".

Di thread lain, `Explainer._worker` mengirim prompt ke Ollama. Kalau berhasil, `Detector.apply_explanation` menyimpan hasilnya dan mencatat `penjelasan_ai`. Kalau gagal, `explanation_failed` mematikan tanda `pending`, dan penjelasan bawaan tetap tampil.

### Langkah 9 · Muncul di layar (≤ 2 detik)

Dashboard memanggil `GET /api/status` setiap 2 detik. `server.py` meneruskannya ke `App.status()`, yang mengumpulkan kejadian, perangkat, dan ringkasan catatan bukti. `web/aplikasi.js` menggambar ulang layar. Kotak "Perlu keputusan Anda" tidak bertambah, karena kejadian kritis ini sudah ditangani otomatis. Kotak "Diisolasi saat ini" menjadi 1.

### Langkah 10 · Petugas bertindak

Petugas mencentang "Periksa langsung panel Genset utama". Browser mengirim:

```
POST /api/insiden/PJS-0002/langkah
X-PJS: 1
{"index": 0, "checked": true, "operator": "Serda Contoh"}
```

`server.py` memeriksa kepala `X-PJS`, lalu memanggil `Detector.set_step(...)`. Hasilnya disimpan dan dicatat sebagai `langkah_dicentang`. Setiap tombol lain bekerja dengan cara yang sama.

## 4. Siklus status kejadian

```
                 ┌───────── Isolasi perangkat ─────────┐
                 │                                      ▼
  (baru) ──► menunggu ◄──── Buka lagi ──┐          diisolasi
                 │                       │              │
          Bukan ancaman                  │       Batalkan isolasi
                 │                       │              │
                 ▼                       │              ▼
           bukan_ancaman ────────────────┘           dilepas ──► (Isolasi lagi / Bukan ancaman)
```

Kejadian kritis pada peralatan langsung masuk `diisolasi` tanpa melewati `menunggu`.

## 5. Isi database

| Tabel | Isi | Kolom penting |
|---|---|---|
| `devices` | Perangkat yang dikenal | `ip`, `mac`, `vendor`, `name`, `zone`, `source` (`konfigurasi`, `masa_belajar`, `baru`) |
| `incidents` | Kejadian | `id`, `kind`, `severity`, `status`, `count`, `isolated_ip`, `explanation` (JSON), `steps` (JSON) |
| `suppressions` | Pasangan yang ditandai bukan ancaman | `kind`, `src_ip`, `dst_ip`, `operator` |
| `meta` | Info kecil | `learning_started`, `incident_counter` |

Lihat isinya sendiri dengan `python -c "import sqlite3; print(sqlite3.connect('data-demo/pjs.sqlite3').execute('select id, kind, status from incidents').fetchall())"`.

## 6. Daftar API

| Permintaan | Fungsi yang dipanggil |
|---|---|
| `GET /api/status` | `App.status()` |
| `POST /api/insiden/<id>/isolasi` | `Detector.isolate(by="operator")` |
| `POST /api/insiden/<id>/lepas` | `Detector.release()` |
| `POST /api/insiden/<id>/bukan-ancaman` | `Detector.dismiss()` |
| `POST /api/insiden/<id>/buka-lagi` | `Detector.reopen()` |
| `POST /api/insiden/<id>/langkah` | `Detector.set_step()` |
| `POST /api/bukti/periksa` | `App.check_integrity()` |
| `GET /laporan/<id>` | Laporan siap cetak, sekaligus `Detector.mark_reported()` |

## 7. Menambah jenis kejadian baru (latihan besar)

Misalnya kamu ingin kotak mengenali **perintah tulis register Modbus** sebagai jenis tersendiri.

1. Tulis aturan Suricata baru (bab 04, latihan 2) dengan `metadata:pjs_jenis ot_tulis_register, pjs_tingkat tinggi;`.
2. Tambahkan entri `"ot_tulis_register"` di `PLAYBOOK` (`pjs/playbook.py`): judul, tingkat, `what`, `why`, `steps`.
3. Tambahkan satu baris contoh di `lab/contoh_eve.jsonl`.
4. Tambahkan tes di `tests/test_detector.py`.
5. Jalankan tes, lalu demo. Kejadian baru tampil lengkap dengan penjelasan dan langkahnya. **Tidak ada kode lain yang perlu diubah.**

## Latihan

1. Jalankan demo dengan `-v` (`python -m pjs -v demo --putar --baru`) dan baca pesan-pesan yang muncul.
2. Pasang titik henti (`breakpoint()`) di awal `Detector._raise`, jalankan `python -m pjs putar` di terminal lain, dan ikuti langkah 6 sampai 8 baris demi baris.
3. Kerjakan latihan besar di bagian 7.
4. Gambar ulang diagram bagian 3 dengan tanganmu sendiri tanpa melihat. Kalau bisa, kamu siap menjelaskannya ke juri.

## Kamu paham kalau...

- bisa menceritakan perjalanan satu serangan dan menunjuk fungsi di setiap langkah,
- tahu kenapa tiga peringatan menjadi satu kejadian,
- bisa menambah jenis kejadian baru tanpa bertanya.
