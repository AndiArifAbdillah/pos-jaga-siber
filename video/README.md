# Pembuat video Pos Jaga Siber

Folder ini berisi semua yang dibutuhkan untuk membuat ulang video presentasi (sekitar 5 menit 40 detik, 1920 × 1080). Video **tidak dibuat dengan AI pembuat video**. Gambarnya berasal dari:

- **dashboard asli** yang direkam saat berjalan dengan model AI lokal,
- **animasi penjelasan** yang digambar di `adegan.html`,
- **narasi** suara bahasa Indonesia dari naskah `naskah.json`.

## Isi folder

| Berkas | Isi |
|---|---|
| `naskah.json` | Naskah: 12 adegan, setiap adegan berisi beberapa ketukan (kalimat) |
| `rekam_dashboard.py` | Menjalankan kotak dalam mode demo, memutar skenario, dan memotret dashboard asli |
| `adegan.html` | Panggung animasi. Setiap adegan bisa diputar ke detik mana pun |
| `buat_video.py` | Membuat suara, menghitung waktu, merender frame, dan menggabungkan semuanya |
| `rekaman.py` | Memakai rekaman suara sendiri: menulis naskah rekaman, membersihkan dan memotong rekaman per kalimat |
| `naskah-rekaman.md` | Naskah bernomor untuk dibaca saat merekam suara sendiri |
| `bahan/` | Hasil `rekam_dashboard.py` (tidak diunggah ke GitHub) |
| `kerja/` | Berkas sementara: suara, potongan adegan, pratinjau (tidak diunggah) |
| `hasil/` | Video jadi `pos-jaga-siber.mp4` dan teks `pos-jaga-siber.srt` (tidak diunggah) |

## Yang dibutuhkan

- Python 3.10+, **ffmpeg**, dan **Microsoft Edge** (sudah ada di Windows).
- Dua pustaka Python:

  ```bash
  python -m pip install playwright edge-tts
  ```

- **Ollama** dengan satu model, supaya penjelasan dan asisten di dashboard memakai AI.
- **Internet** saat membuat suara. Yang dikirim ke layanan suara Microsoft hanya teks naskah.

## Cara membuat video

Jalankan dari folder proyek:

```bash
python video/rekam_dashboard.py --model qwen3.5-4b:latest
```

Ganti nama model dengan model yang ada di `ollama list`. Langkah ini memakan sekitar 3–4 menit dan menjalankan kotak sendiri di port 8095, jadi demo lain di port 8080 tidak terganggu.

```bash
python video/buat_video.py --pratinjau
```

Langkah ini membuat beberapa gambar contoh per adegan di `video/kerja/pratinjau/`. Periksa dulu sebelum merender penuh.

```bash
python video/buat_video.py
```

Render penuh memakan sekitar 10–15 menit. Hasilnya di `video/hasil/pos-jaga-siber.mp4`. Kalau render terhenti di tengah jalan, tambahkan `--lanjut` supaya adegan yang sudah jadi tidak dirender ulang.

## Mengubah video

- **Kalimat narasi:** ubah `teks` di `naskah.json`. Kalau ada angka atau singkatan yang dibaca aneh, isi juga `ucap` dengan cara bacanya, misalnya `"teks": "48 MB"` dan `"ucap": "empat puluh delapan megabita"`.
- **Suara:** ubah `suara` di `naskah.json`. Pilihannya `id-ID-ArdiNeural` (laki-laki) atau `id-ID-GadisNeural` (perempuan). Bisa juga suara multibahasa seperti `en-US-AndrewMultilingualNeural`, yang membaca bahasa Indonesia sekaligus mengucapkan kata Inggris dengan benar.
- **Cara baca istilah:** atur di bagian `lafal` di `naskah.json`. Contohnya, "AI" dibaca "ei ai". Suara id-ID membaca kata Inggris dengan ejaan Indonesia ("machine learning" jadi "macin learninang"), jadi istilah Inggris ditulis sesuai bunyinya di `lafal.suara_indonesia`, misalnya `"machine learning": "masyin lerning"`. Teks di layar tetap memakai tulisan aslinya.
- **Gerakan kamera dan sorotan di dashboard:** ubah bagian `LAYAR` di `adegan.html`.
- **Satu adegan saja:** `python video/buat_video.py --adegan solusi`.

Waktu animasi mengikuti narasi. Kalau satu kalimat diubah, animasi adegan itu ikut bergeser otomatis.

## Memakai suara sendiri

Juri biasanya lebih menghargai suara tim sendiri, dan suara manusia jauh lebih hidup daripada suara buatan. Kamu tidak perlu membaca mengikuti video. Video yang menyesuaikan waktunya dengan suaramu.

1. Buka [`naskah-rekaman.md`](naskah-rekaman.md). Isinya 41 kalimat bernomor, dengan arahan gaya baca di setiap adegan. Kalau naskah diubah, buat ulang dengan `python video/rekaman.py naskah`.
2. Rekam dengan HP. Boleh satu berkas panjang, boleh juga beberapa berkas berurutan. **Diam sekitar 2 detik di antara kalimat.** Kalau salah, diam sebentar lalu ulangi kalimat itu. Yang dipakai adalah ulangan terakhir.
3. Periksa hasil pemotongannya:

   ```bash
   python video/rekaman.py cek rekaman.m4a
   ```

   Tabelnya menunjukkan bagian rekaman yang dipakai untuk setiap kalimat. Kalimat yang panjangnya jauh dari perkiraan ditandai "periksa". Potongan per kalimat ada di `video/kerja/rekaman/kalimat-NN.wav`, jadi bisa didengarkan satu per satu.
4. Buat videonya:

   ```bash
   python video/buat_video.py --rekaman rekaman.m4a
   ```

   Kalau rekamannya beberapa berkas, tulis semuanya berurutan: `--rekaman adegan1.m4a adegan2.m4a ...`.

Yang dilakukan pada rekaman:
- Dengung rendah dibuang dan desis latar dikurangi.
- Kekerasan suara disamakan dengan standar video, tanpa meratakan keras-lembutnya, supaya ekspresi bicara tetap utuh.
- Rekaman dipotong per kalimat, dengan bantuan jeda diam di antara kalimat.
- Setiap potongan dicocokkan dengan kalimat naskah berdasarkan panjangnya. Potongan yang tidak cocok dilewati, misalnya ulangan atau batuk.

Kalau ada kalimat yang tertukar, salin `video/kerja/rekaman/pemetaan-otomatis.json` menjadi `pemetaan.json` di folder yang sama. Ubah angka detik awal dan akhir kalimat itu, lalu jalankan lagi. Nama pembaca di deskripsi YouTube diambil dari `pembaca_rekaman` di `naskah.json`.

## Kejujuran isi video

- Adegan dashboard memakai **contoh catatan sensor** (mode demo), dan blokirnya **mode uji**. Ini tertulis di atas setiap rekaman dashboard dan disebut di narasi.
- Adegan genset tiruan adalah **serangan sungguhan ke genset tiruan** di laptop. Keluaran terminal dan lampunya asli.
- Kalau lab VirtualBox sudah jadi, rekaman lab (MikroTik sungguhan memblokir penyerang) sebaiknya ditambahkan. Lihat [docs/CARA-DEMO.md](../docs/CARA-DEMO.md) bagian B.
