# Pos Jaga Siber

Penjaga jaringan untuk markas satuan. Kotak ini **bekerja mandiri**: tetap menjaga meskipun internet putus, dan data markas tidak dikirim keluar.

Purwarupa untuk **Kartika Cyber Hackathon 2026**, kategori **Defensive Shield**.

## Apa yang dilakukan kotak ini

1. **Mengawasi** semua lalu lintas di jaringan kantor dan jaringan peralatan (genset, kamera, kunci pintu).
2. **Mengenali** perangkat yang biasa ada, lalu memberi tahu kalau ada perangkat baru.
3. **Mendeteksi** kejadian berbahaya, misalnya perintah asing ke genset, kamera yang mengirim rekaman ke luar, atau laptop yang diam-diam "melapor" ke alamat luar.
4. **Bertindak cepat**: kejadian kritis pada peralatan langsung diisolasi lewat router MikroTik. Kejadian lain diputuskan oleh petugas jaga.
5. **Menjelaskan** setiap kejadian dalam bahasa sehari-hari (AI lokal), lengkap dengan langkah SOP yang bisa dicentang.
6. **Mencatat** semua kejadian dan tindakan di catatan bukti anti-ubah. Satu entri yang diubah atau dihapus langsung ketahuan.

## Coba dalam 1 menit (tanpa alat apa pun)

Butuh Python 3.10 atau lebih baru. Tidak perlu memasang pustaka tambahan.

```bash
git clone https://github.com/AndiArifAbdillah/pos-jaga-siber.git
cd pos-jaga-siber
python -m pjs demo --putar --baru
```

Buka **http://localhost:8080**. Dalam sekitar 40 detik, tiga skenario muncul di dashboard:

| Skenario | Yang terjadi | Yang dilakukan kotak |
|---|---|---|
| Laptop asing mematikan genset | Perintah tulis ke genset dari perangkat yang bukan pengendali | Kritis: diisolasi otomatis, lalu dijelaskan |
| Kamera mengirim data ke luar | Kamera gerbang mengunggah 48 MB ke alamat luar | Tinggi: dijelaskan, petugas memutuskan |
| Laptop staf "melapor" teratur | Sambungan ke alamat luar setiap 2 detik, sangat teratur | Tinggi: dijelaskan, petugas memutuskan |

Skenario keempat (catatan bukti diubah):

```bash
python lab/ubah_catatan.py
```

Lalu tekan **Periksa sekarang** di dashboard. Layar berubah merah dan menunjukkan entri mana yang hilang.

Panduan lengkap langkah demi langkah, termasuk mode rekam video, AI lokal, dan jalan keluar kalau ada masalah: [docs/CARA-MENJALANKAN.md](docs/CARA-MENJALANKAN.md).

## Cara kerja singkat

```
                     ┌──────────────────── Kotak Pos Jaga ────────────────────┐
 lalu lintas ──────► │ Suricata ──► eve.json ──► pjs (detector)               │
 (salinan dari       │                              │                          │
  router/switch)     │                 ┌────────────┼──────────────┐           │
                     │                 ▼            ▼              ▼           │
                     │          MikroTik API   AI lokal      catatan bukti     │
                     │          (isolasi)      (Ollama)      (rantai hash)     │
                     │                 └────────────┼──────────────┘           │
                     │                              ▼                          │
                     │                  dashboard operator :8080               │
                     └─────────────────────────────────────────────────────────┘
```

Penjelasan lengkap dari nol ada di [docs/belajar](docs/belajar/00-mulai-di-sini.md).

## Isi folder

| Folder / berkas | Isi |
|---|---|
| `pjs/` | Program kotak (Python, tanpa pustaka tambahan) |
| `web/` | Dashboard operator (HTML, CSS, JavaScript) |
| `aturan/` | Aturan Suricata khusus peralatan, potongan `suricata.yaml`, skrip MikroTik |
| `lab/` | Genset tiruan, simulasi serangan, pembuat lalu lintas, contoh data, kode ESP32 lampu |
| `tests/` | Tes otomatis |
| `docs/belajar/` | Dokumen belajar dari dasar sampai paham seluruh proyek |
| `docs/CARA-MENJALANKAN.md` | Cara menjalankan proyek di laptop biasa, langkah demi langkah |
| `docs/PANDUAN-LAB.md` | Langkah menyusun lab virtual di satu laptop |
| `docs/PEMBAGIAN-KERJA.md` | Pembagian kerja tim 2 orang sampai 14 November |
| `config.demo.json` | Konfigurasi demo (tanpa Suricata, tanpa MikroTik) |
| `config.contoh.json` | Contoh konfigurasi untuk kotak sungguhan |

## Perintah

| Perintah | Kegunaan |
|---|---|
| `python -m pjs demo --putar --baru` | Demo lengkap di satu laptop |
| `python -m pjs --config config.json jalan` | Menjalankan kotak sungguhan |
| `python -m pjs putar --langkah` | Memutar contoh skenario satu per satu (tekan Enter) |
| `python -m pjs periksa` | Memeriksa rantai catatan bukti |
| `python -m pjs kode` | Menampilkan kode buku jaga |
| `python -m pjs cek-kode A1B2-C3D4` | Mencocokkan kode dari buku jaga |
| `python -m pjs uji-mikrotik` | Mencoba sambungan ke MikroTik |
| `python -m pjs uji-ai` | Mencoba penjelas AI |
| `python lab/genset_tiruan.py` | Genset tiruan (Modbus) dengan halaman lampu di port 8081 |

## Tes

```bash
python -m unittest discover -s tests -t .
```

## Batas purwarupa

Ditulis terus terang supaya tidak ada klaim berlebihan:

- Dashboard belum memakai login. Pasang hanya di jaringan pengelolaan yang terbatas.
- Kunci tanda tangan disimpan di berkas. Versi lanjut sebaiknya memakai chip TPM.
- Aturan dasar masih sederhana: perangkat baru, peralatan ke luar markas, sinyal berkala, dan aturan Suricata.
- Langkah SOP di `pjs/playbook.py` adalah contoh dan harus diganti dengan SOP resmi satuan.
- Belum diuji di jaringan satuan sungguhan. Uji coba baru di lab virtual.
- Dashboard pusat (gabungan banyak kotak) belum dibuat.
