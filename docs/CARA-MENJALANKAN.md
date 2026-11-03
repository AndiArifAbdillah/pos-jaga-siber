# Cara menjalankan Pos Jaga Siber

Panduan ini untuk menjalankan proyek di **laptop biasa** (Windows, Linux, atau Mac) tanpa alat jaringan apa pun. Untuk lab lengkap dengan Suricata dan MikroTik, lihat [PANDUAN-LAB.md](PANDUAN-LAB.md).

## 1. Yang perlu dipasang dulu

| Program | Gunanya | Cara cek sudah terpasang |
|---|---|---|
| **Python 3.10 atau lebih baru** | Menjalankan kotak | `python --version` |
| **Git** | Mengambil dan memperbarui kode dari GitHub | `git --version` |
| Browser apa saja | Membuka dashboard | - |

Kalau `python` belum ada, unduh dari python.org. Saat memasang di Windows, **centang "Add python.exe to PATH"** di layar pertama.

Proyek ini **tidak butuh** `pip install` apa pun.

## 2. Mengambil kode

Repositori ini privat. Kamu harus diundang dulu sebagai kolaborator di GitHub, lalu terima undangan yang masuk ke email.

```bash
git clone https://github.com/AndiArifAbdillah/pos-jaga-siber.git
cd pos-jaga-siber
```

Kalau tidak memakai Git, buka halaman repositori di GitHub, tekan **Code → Download ZIP**, lalu ekstrak.

Kalau proyek sudah ada di laptopmu, cukup masuk ke foldernya. Contoh di Windows:

```bash
cd "D:\WORK\HAckthon cyber\pos-jaga-siber"
```

Setiap kali mulai kerja, ambil perubahan terbaru dari pasanganmu:

```bash
git pull
```

## 3. Menjalankan demo

```bash
python -m pjs demo --putar --baru
```

Di Linux dan Mac, ganti `python` dengan `python3`.

Arti pilihannya:

| Pilihan | Arti |
|---|---|
| `demo` | Jalankan kotak dengan konfigurasi demo (`config.demo.json`), tanpa Suricata dan tanpa MikroTik |
| `--putar` | Putar otomatis contoh skenario serangan |
| `--baru` | Hapus data demo lama, mulai dari nol |

Terminal akan menampilkan:

```
Pos Jaga Siber berjalan. Buka http://localhost:8080
```

**Biarkan terminal ini tetap terbuka.** Kalau ditutup, kotaknya ikut mati.

## 4. Membuka dashboard

Buka browser ke **http://localhost:8080**. Dalam sekitar 40 detik, tiga kejadian muncul:

| Kejadian | Tingkat | Yang dilakukan kotak |
|---|---|---|
| Perintah asing ke Genset utama | Kritis | Langsung diisolasi otomatis |
| Kamera Gerbang Utama mengirim data ke luar markas | Tinggi | Menunggu keputusan petugas |
| Laptop Staf Operasi menghubungi alamat luar secara teratur | Tinggi | Menunggu keputusan petugas |

Ada juga kejadian "Ada perangkat baru di jaringan", karena laptop penyerang belum pernah terlihat sebelumnya.

Yang bisa dicoba:

- klik kejadian untuk membaca penjelasannya,
- centang langkah SOP,
- tekan **Isolasi perangkat**, **Bukan ancaman**, atau **Batalkan isolasi**,
- tekan **Buat laporan** untuk laporan siap cetak,
- ganti nama operator di kanan atas.

Setiap tindakanmu muncul di panel **Catatan bukti** di kanan bawah.

## 5. Skenario 4: catatan bukti diubah

Buka **terminal kedua** di folder proyek yang sama, lalu jalankan:

```bash
python lab/ubah_catatan.py
```

Skrip ini menghapus satu entri dari catatan bukti, seolah-olah ada orang yang menghapus jejak. Kembali ke dashboard, lalu tekan **Periksa sekarang**. Layar berubah merah dan menyebut entri mana yang hilang.

Untuk mengulang dari awal, matikan kotak lalu jalankan lagi perintah demo dengan `--baru`.

## 6. Mematikan kotak

Tekan **Ctrl+C** di terminal tempat kotak berjalan.

## 7. Untuk rekam video: skenario satu per satu

Supaya bisa bercerita dulu sebelum setiap serangan, jalankan kotak dan pemutar skenario secara terpisah.

**Terminal 1**, jalankan kotak tanpa memutar skenario:

```bash
python -m pjs demo --baru
```

**Terminal 2**, putar skenario. Perintah ini menunggu kamu menekan **Enter** sebelum setiap skenario:

```bash
python -m pjs --config config.demo.json putar --langkah
```

## 8. Tambahan (tidak wajib)

### Halaman lampu genset

```bash
python lab/genset_tiruan.py
```

Buka **http://localhost:8081**. Di terminal lain, matikan genset tiruan:

```bash
python lab/serangan_genset.py --target 127.0.0.1 --port 5020
```

Lampu di halaman itu padam. Tekan **Nyalakan dari panel** untuk menyalakannya lagi.

Di satu laptop, genset tiruan ini **belum tersambung ke dashboard**, karena belum ada Suricata yang mengawasi lalu lintasnya. Keduanya baru tersambung di lab virtual.

### Penjelasan dari AI lokal

Tanpa AI, dashboard tetap menampilkan penjelasan bawaan. Untuk mencoba AI:

1. Pasang **Ollama** dari ollama.com.
2. Unduh model (sekali saja, butuh internet):

   ```bash
   ollama pull qwen2.5:1.5b
   ```

3. Cek apakah kotak bisa memakainya:

   ```bash
   python -m pjs --config config.demo.json uji-ai
   ```

4. Jalankan ulang demo. Tanda di kanan atas dashboard berubah menjadi **"AI lokal: siap"**, dan penjelasan kejadian ditulis ulang oleh AI.

### Tes otomatis

```bash
python -m unittest discover -s tests -t .
```

Hasil yang benar diakhiri dengan `OK`.

### Perintah lain

| Perintah | Kegunaan |
|---|---|
| `python -m pjs --config config.demo.json kode` | Menampilkan kode buku jaga saat ini |
| `python -m pjs --config config.demo.json periksa` | Memeriksa rantai catatan bukti dari terminal |
| `python -m pjs --config config.demo.json cek-kode A1B2-C3D4` | Mencocokkan kode dari buku jaga |
| `python -m pjs --help` | Daftar semua perintah |

## 9. Kalau ada masalah

| Gejala | Jalan keluar |
|---|---|
| `'python' is not recognized` | Python belum terpasang atau belum masuk PATH. Pasang ulang dan centang "Add python.exe to PATH". Di Windows, coba juga `py` sebagai ganti `python` |
| `No module named pjs` | Terminal belum berada di folder proyek. Jalankan `cd` ke folder `pos-jaga-siber` dulu |
| Galat `Address already in use` atau `WinError 10048` (port 8080 terpakai) | Kotak lain masih berjalan, atau program lain memakai port itu. Tutup yang lama, atau jalankan dengan port lain: `python -m pjs demo --putar --baru --port 8090`, lalu buka http://localhost:8090 |
| Dashboard kosong, tidak ada kejadian | Pastikan memakai `--putar`, lalu tunggu sekitar 40 detik |
| Banner "Dashboard terputus dari kotak" | Terminal kotak tertutup atau kotak berhenti. Jalankan lagi perintah demo |
| Layar merah "Catatan bukti rusak" padahal tidak sengaja | Skenario 4 pernah dijalankan. Mulai ulang dengan `--baru` |
| Tanda kanan atas "AI lokal: tidak tersambung" | Normal kalau Ollama belum dipasang. Penjelasan bawaan tetap tampil |
| `git clone` meminta masuk atau gagal | Kamu belum diundang atau belum menerima undangan kolaborator |

## Langkah berikutnya

- Pahami cara kerjanya dari nol: [belajar/00-mulai-di-sini.md](belajar/00-mulai-di-sini.md)
- Susun lab lengkap dengan Suricata dan MikroTik: [PANDUAN-LAB.md](PANDUAN-LAB.md)
- Pembagian kerja dan jadwal: [PEMBAGIAN-KERJA.md](PEMBAGIAN-KERJA.md)
