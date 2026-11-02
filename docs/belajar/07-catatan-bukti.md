# 07 · Catatan bukti: buku jaga digital yang tidak bisa diubah diam-diam

## 1. Masalahnya

Setelah serangan, pertanyaan pertama komandan: **"Apa yang terjadi, kapan, dan siapa yang bertindak?"** Jawabannya ada di catatan kejadian. Masalahnya, penyerang yang pintar, atau orang dalam yang lalai, akan **menghapus atau mengubah catatan** itu. Catatan biasa di berkas teks bisa diubah siapa saja tanpa jejak.

Kotak ini membuat catatan yang **ketahuan kalau diubah**. Ada tiga lapis pengaman:

1. **Rantai sidik jari (hash chain)**: setiap entri tersambung ke entri sebelumnya.
2. **Tanda tangan digital**: setiap entri ditandatangani kunci rahasia milik kotak.
3. **Saksi di luar kotak**: kode buku jaga yang ditulis di kertas setiap ganti piket.

## 2. Sidik jari digital (hash)

Fungsi **hash** mengubah data sebesar apa pun menjadi "sidik jari" pendek berukuran tetap. Kotak memakai **SHA-256**, yang hasilnya 256 bit, ditulis sebagai 64 huruf heksadesimal.

Coba di Python:

```python
import hashlib
print(hashlib.sha256(b"genset mati jam 15.20").hexdigest())
print(hashlib.sha256(b"genset mati jam 15.21").hexdigest())
```

Satu angka berubah, sidik jarinya berubah total. Sifat-sifat penting SHA-256:

| Sifat | Artinya |
|---|---|
| Tetap | Data sama selalu menghasilkan sidik jari sama |
| Berubah total | Beda satu huruf saja, hasilnya sama sekali lain |
| Satu arah | Dari sidik jari, data aslinya tidak bisa ditebak |
| Tidak bertabrakan | Praktis mustahil menemukan dua data berbeda dengan sidik jari sama |

## 3. Rantai sidik jari

Setiap entri catatan menyimpan sidik jari **entri sebelumnya** (`prev`), lalu sidik jari dirinya sendiri (`hash`) dihitung dari isinya **termasuk** `prev`:

```
┌──────── #1 ────────┐   ┌──────── #2 ────────┐   ┌──────── #3 ────────┐
│ kotak dinyalakan    │   │ kejadian PJS-0001  │   │ isolasi otomatis   │
│ prev: 0000...0000   │◄──│ prev: a1b2...      │◄──│ prev: 9f3c...      │
│ hash: a1b2...       │   │ hash: 9f3c...      │   │ hash: 3de4...      │
└─────────────────────┘   └────────────────────┘   └────────────────────┘
```

Kalau seseorang **mengubah** entri #2, `hash` #2 yang dihitung ulang tidak cocok lagi dengan yang tersimpan. Kalau ia **menghapus** entri #2, entri #3 menunjuk ke `prev` yang tidak ada, dan nomor urut melompat dari #1 ke #3. Pemeriksaan (`EvidenceLog.verify`) menemukan keduanya dan menyebut nomor entrinya.

Satu baris di `bukti.jsonl`:

```json
{"seq": 4, "time": "2026-11-12T15:19:58+07:00", "kind": "isolasi_otomatis",
 "data": {"incident": "PJS-0002", "ip": "10.10.0.66", "mode": "mikrotik", "operator": null},
 "prev": "9f3c...", "hash": "3de4...", "sig": "5b1a..."}
```

### Kenapa harus "JSON kanonik"?

Sidik jari dihitung dari teks. `{"a":1,"b":2}` dan `{"b":2,"a":1}` artinya sama, tetapi teksnya beda, jadi sidik jarinya beda. Fungsi `canonical()` selalu mengurutkan kunci dan membuang spasi, sehingga isi yang sama selalu menghasilkan sidik jari yang sama.

## 4. Kenapa rantai saja tidak cukup

Penyerang yang pintar bisa mengubah entri #2, lalu **menghitung ulang** semua hash setelahnya. Rantainya kembali tampak utuh. Karena itu dibutuhkan lapis kedua.

## 5. Tanda tangan digital (Ed25519)

Tanda tangan digital memakai **sepasang kunci**:

- **Kunci rahasia** (`data/kunci_kotak.key`): hanya kotak yang punya. Dipakai **menandatangani**.
- **Kunci publik** (`data/kunci_kotak.pub`): boleh dibagikan ke siapa saja. Dipakai **memeriksa** tanda tangan.

Setiap entri, sidik jarinya ditandatangani (`sig`). Penyerang yang menghitung ulang hash tidak bisa membuat tanda tangan baru tanpa kunci rahasia. Pemeriksaan langsung menemukan "Tanda tangan entri #… tidak sah".

Kotak memakai algoritma **Ed25519** (standar RFC 8032): kunci 32 byte, tanda tangan 64 byte, cepat dan aman. Kode memakai pustaka `cryptography` kalau terpasang, dan kalau tidak ada, memakai `pjs/ed25519_pure.py` (Python murni). Tes `tests/test_evidence.py` memastikan keduanya menghasilkan tanda tangan yang **persis sama**, dan cocok dengan contoh resmi di RFC 8032.

## 6. Saksi di luar kotak

Masih ada dua celah:

1. **Memotong ekor:** penyerang menghapus 5 entri terakhir. Rantai sisanya tetap utuh dan tanda tangannya sah.
2. **Mencuri kunci rahasia:** dengan kunci, penyerang bisa menulis ulang seluruh catatan.

Penangkalnya: **saksi yang tidak bisa disentuh penyerang.**

- **Kode buku jaga.** Dashboard menampilkan 8 huruf pertama sidik jari entri terakhir, misalnya `3DE4-D46D`. Setiap ganti piket, petugas menyalinnya ke **buku jaga kertas**. Kalau suatu saat kode itu tidak ditemukan di catatan (`python -m pjs cek-kode 3DE4-D46D`), artinya catatan sudah dipotong atau ditulis ulang.
- **Pusat (rencana lanjutan).** Saat tersambung, kotak mengirim sidik jari terakhir ke server pusat. Pusat menjadi saksi kedua.
- **TPM (rencana lanjutan).** Kunci rahasia disimpan di chip keamanan, sehingga tidak bisa disalin keluar.

## 7. Ini blockchain atau bukan?

Jawaban jujur untuk juri: **ini memakai prinsip inti blockchain, tetapi bukan blockchain penuh.**

| | Blockchain penuh (misalnya Bitcoin) | Catatan bukti PJS |
|---|---|---|
| Rantai hash | Ya | Ya |
| Tanda tangan digital | Ya | Ya |
| Banyak pihak menyimpan salinan | Ya, ribuan komputer | Kotak, ditambah saksi kode buku jaga dan pusat |
| Kesepakatan antar banyak pihak (konsensus) | Ya, mahal dan lambat | Tidak perlu, karena hanya satu penulis (kotak) |
| Butuh jaringan terus-menerus | Ya | Tidak |

Konsensus dibutuhkan kalau banyak pihak yang tidak saling percaya menulis ke catatan yang sama. Di sini hanya kotak yang menulis. Yang dibutuhkan hanya **bukti bahwa catatan tidak diubah**, dan itu sudah dipenuhi oleh rantai, tanda tangan, dan saksi.

## Latihan

1. Jalankan demo, lalu:

   ```bash
   python -m pjs --config config.demo.json kode
   python lab/ubah_catatan.py --ubah 3
   python -m pjs --config config.demo.json periksa
   ```

   Pesan apa yang muncul? Kenapa yang terdeteksi "isi diubah" dan bukan "entri hilang"?

2. Pulihkan dari cadangan (matikan kotak dulu), lalu coba `--hapus 5`. Pesan apa yang muncul sekarang?
3. Buka `tests/test_evidence.py`, baca `test_rewritten_hash_without_key_fails_signature`. Jelaskan dengan kata-katamu sendiri apa yang diuji.
4. Kenapa kode buku jaga ditulis di **kertas**, bukan di komputer lain di markas?

## Kamu paham kalau...

- bisa menjelaskan dengan gambar kenapa mengubah satu entri merusak rantai,
- bisa menjelaskan kenapa tanda tangan dibutuhkan selain rantai,
- bisa menjawab "ini blockchain atau bukan?" dengan jujur dan yakin.
