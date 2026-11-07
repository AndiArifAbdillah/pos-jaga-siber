# Pembuat video Pos Jaga Siber

Folder ini berisi semua yang dibutuhkan untuk membuat ulang video presentasi (sekitar 4 menit 48 detik, 1920 × 1080). Video **tidak dibuat dengan AI pembuat video**. Gambarnya berasal dari:

- **dashboard asli** yang direkam saat berjalan dengan model AI lokal,
- **animasi penjelasan** yang digambar di `adegan.html`,
- **narasi** suara bahasa Indonesia dari naskah `naskah.json`.

## Isi folder

| Berkas | Isi |
|---|---|
| `naskah.json` | Naskah: 11 adegan, setiap adegan berisi beberapa ketukan (kalimat) |
| `rekam_dashboard.py` | Menjalankan kotak dalam mode demo, memutar skenario, dan memotret dashboard asli |
| `adegan.html` | Panggung animasi. Setiap adegan bisa diputar ke detik mana pun |
| `buat_video.py` | Membuat suara, menghitung waktu, merender frame, dan menggabungkan semuanya |
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
- **Suara:** ubah `suara` di `naskah.json`. Pilihannya `id-ID-ArdiNeural` (laki-laki) atau `id-ID-GadisNeural` (perempuan).
- **Gerakan kamera dan sorotan di dashboard:** ubah bagian `LAYAR` di `adegan.html`.
- **Satu adegan saja:** `python video/buat_video.py --adegan solusi`.

Waktu animasi mengikuti narasi. Kalau satu kalimat diubah, animasi adegan itu ikut bergeser otomatis.

## Memakai suara sendiri

Juri biasanya lebih menghargai suara tim sendiri:

1. Putar `pos-jaga-siber.mp4` tanpa suara, lalu rekam diri kalian membaca teks yang muncul di layar, mengikuti waktunya.
2. Gabungkan rekamannya dengan video:

   ```bash
   ffmpeg -i video/hasil/pos-jaga-siber.mp4 -i suara-tim.m4a -map 0:v -map 1:a -c:v copy -c:a aac -shortest video/hasil/pos-jaga-siber-suara-tim.mp4
   ```

## Kejujuran isi video

- Adegan dashboard memakai **contoh catatan sensor** (mode demo), dan blokirnya **mode uji**. Ini tertulis di atas setiap rekaman dashboard dan disebut di narasi.
- Adegan genset tiruan adalah **serangan sungguhan ke genset tiruan** di laptop. Keluaran terminal dan lampunya asli.
- Kalau lab VirtualBox sudah jadi, rekaman lab (MikroTik sungguhan memblokir penyerang) sebaiknya ditambahkan. Lihat [docs/CARA-DEMO.md](../docs/CARA-DEMO.md) bagian B.
