# 13 · AI deteksi perilaku dan asisten piket

Tema lomba adalah **pemanfaatan AI untuk pengamanan IT/OT**, dan kriteria "Inovasi Teknis Berbasis AI" bernilai 25%. Bab ini menjelaskan tiga cara kotak memakai AI, terutama dua yang belum dibahas di bab 06.

| AI | Tugas | Jenis AI | Berkas |
|---|---|---|---|
| **Mata kedua** | Menemukan perangkat yang berperilaku aneh, termasuk serangan yang belum punya aturan | Machine learning (Isolation Forest) | `pjs/anomaly.py` |
| **Penjelas** | Menjelaskan setiap kejadian dalam bahasa sehari-hari | Model bahasa lokal (LLM) | `pjs/explainer.py` (bab 06) |
| **Asisten piket** | Menjawab pertanyaan petugas dan menyusun laporan ganti piket | Model bahasa lokal (LLM) | `pjs/assistant.py` |

Prinsip yang sama berlaku untuk ketiganya: **AI menemukan dan menjelaskan, sedangkan aturan tetap dan manusia yang memutuskan.** Tidak ada AI yang bisa memblokir.

## Bagian A · AI deteksi perilaku

### 1. Kenapa aturan saja tidak cukup

Aturan Suricata seperti daftar wajah buronan: hanya mengenali yang sudah pernah tercatat. Penyerang baru, atau cara serangan baru (sering disebut **zero-day**), lolos dari daftar itu.

Cara lain adalah mengenali **kebiasaan**. Petugas jaga yang sudah lama bertugas tahu kebiasaan markasnya: truk logistik datang pagi, lampu gudang padam jam 22.00. Kalau ada yang tidak biasa, ia curiga walaupun tidak tahu apa persisnya. AI deteksi perilaku meniru cara berpikir ini.

### 2. Dari lalu lintas menjadi angka

Setiap **rentang waktu** (bawaan 5 menit, di demo 10 detik), kegiatan setiap perangkat diringkas menjadi tujuh angka ciri:

| Ciri | Contoh normal kamera | Contoh kunci pintu yang dikuasai penyerang |
|---|---|---|
| Jumlah sambungan | 1 | 14 |
| Jumlah perangkat/alamat yang dihubungi | 1 (perekam CCTV) | 14 |
| Jumlah jenis layanan (port) | 1 | 4 |
| Data dikirim | 1,2 MB | 1 KB |
| Data diterima | 9 KB | 0,4 KB |
| Sambungan ke luar markas | 0 | 0 |
| Jam | 15 | 15 |

Bahannya hanya catatan `flow` Suricata (siapa ke siapa, berapa banyak), **bukan isi percakapan**.

### 3. Masa belajar

Selama masa belajar (bawaan 14 hari), setiap ringkasan disimpan sebagai contoh "normal" di tabel `behavior_samples`. Setelah masa belajar selesai, kotak melatih model **per jaringan**: satu untuk jaringan peralatan, satu untuk jaringan kantor. Pemisahan ini penting, karena laptop yang menghubungi 10 alamat internet itu wajar, sedangkan genset yang melakukannya sangat tidak wajar.

Model butuh minimal 200 contoh per jaringan (`min_samples`). Kalau kurang, dashboard menulis "AI perilaku: contoh normal belum cukup".

Di demo tidak ada waktu belajar 14 hari, jadi model dilatih dari **contoh buatan** `lab/contoh_riwayat_normal.jsonl` (800 contoh, dibuat oleh `lab/buat_riwayat_normal.py`). Ini harus dikatakan terus terang ke juri.

### 4. Isolation Forest

Isolation Forest (Liu, Ting, dan Zhou, 2008) adalah algoritma machine learning untuk menemukan data yang aneh. Gagasannya sederhana:

> Data yang aneh lebih mudah **dipisahkan** dari kerumunan.

Bayangkan sekumpulan titik. Pilih satu ciri secara acak, lalu belah di posisi acak. Ulangi untuk setiap belahan. Titik yang berada di tengah kerumunan butuh **banyak** belahan sampai terpisah sendirian. Titik yang menyendiri terpisah setelah **sedikit** belahan.

```
                  normal: butuh 8 belahan            aneh: cukup 2 belahan
  ●●●●●●●●●●●  ─────────────────────────►      ●●●●●●●●●●         ○  ◄── terpisah cepat
  ●●●●●●●●●●●                                  ●●●●●●●●●●
```

Satu pohon belahan acak bisa kebetulan salah, jadi dibuat **100 pohon** dan diambil rata-rata panjang jalurnya. Hasilnya diubah menjadi **skor keanehan 0–1**: sekitar 0,5 ke bawah berarti biasa, mendekati 1 berarti sangat aneh.

Kode lengkapnya ada di kelas `IsolationForest` (`pjs/anomaly.py`), sekitar 50 baris Python murni:

- `fit`: membuat 100 pohon, masing-masing dari 256 contoh acak,
- `_build`: membelah secara acak sampai kedalaman tertentu,
- `_path_length`: menghitung berapa belahan sampai sebuah data terpisah,
- `score`: mengubah rata-rata panjang jalur menjadi skor 0–1 dengan rumus `2^(-rata-rata / c(n))`. `c(n)` adalah panjang jalur rata-rata yang diharapkan untuk n data.

### 5. Kenapa ada "penilaian dua sisi"

Saat diuji, Isolation Forest murni punya dua kelemahan nyata:

1. **Ciri yang di data latih selalu sama diabaikan.** Peralatan tidak pernah menghubungi luar markas, jadi ciri "sambungan ke luar" selalu 0. Pohon tidak pernah membelah ciri itu, sehingga kamera yang tiba-tiba mengirim keluar tidak dianggap aneh.
2. **Nilai yang jauh melampaui contoh normal tidak selalu cepat terpisah.** Kalau nilai itu melampaui sisi yang ramai, ia ikut terjebak di kerumunan.

Karena itu kotak menilai dari **dua sisi** dan memakai skor tertinggi:

| Sisi | Cara kerja | Menangkap |
|---|---|---|
| Pola gabungan | Skor Isolation Forest, tetapi baru dihitung kalau lebih aneh daripada 99,5% contoh normal (dikalibrasi dari data latih) | Gabungan ciri yang janggal |
| Batas kebiasaan | Ciri yang melewati angka tertinggi yang pernah terlihat saat belajar | Lonjakan yang jelas, termasuk ciri yang biasanya selalu 0 |

Jam aktif yang hampir tidak pernah dipakai (kurang dari 0,5% contoh) menambah skor ringan.

Hasil uji dengan data demo:

| Kasus | Skor | Ditandai? |
|---|---|---|
| PC pengendali membaca genset (normal) | 0,61 | Tidak |
| Kamera mengirim video ke perekam (normal) | 0,47 | Tidak |
| Laptop staf yang sibuk (normal) | di bawah ambang | Tidak |
| Kamera mengirim 48 MB ke luar markas | 0,97 | Ya |
| Kunci pintu menghubungi 14 alamat dalam 10 detik | 1,00 | Ya |
| **800 contoh normal** | | **0 yang ditandai** |

### 6. Dari skor menjadi kejadian

```
skor < 0,62               → diabaikan
0,62 ≤ skor < 0,72        → kejadian "Perilaku tidak biasa", tingkat sedang
skor ≥ 0,72               → kejadian "Perilaku tidak biasa", tingkat tinggi
```

Kalau perangkat itu **sudah punya kejadian terbuka** dari aturan lain (misalnya kamera sudah tertangkap aturan "peralatan ke luar markas"), kotak tidak membuat kejadian baru. Skor AI **ditempelkan** ke kejadian yang sudah ada sebagai penguat. Di dashboard terlihat kotak biru "AI deteksi perilaku" dengan skornya.

Kejadian dari AI **tidak pernah diisolasi otomatis**. Tingkatnya paling tinggi "tinggi", tidak pernah "kritis".

### 7. Penjelasan yang bisa dipahami

Skor saja tidak berarti bagi petugas. Fungsi `explain` mengubahnya menjadi kalimat dengan membandingkan setiap ciri dengan kebiasaannya:

> AI deteksi perilaku menilai Kunci Pintu Gudang Senjata bertingkah sangat berbeda dari kebiasaannya: menghubungi 14 perangkat atau alamat berbeda dalam 10 detik (biasanya paling banyak 2), membuat 14 sambungan dalam 10 detik (biasanya paling banyak 4), dan mencoba 4 jenis layanan berbeda (biasanya paling banyak 2).

Ini disebut **AI yang bisa dijelaskan** (*explainable AI*): petugas dan juri bisa melihat alasannya, bukan hanya angkanya.

### 8. Batas yang harus diakui

- Di demo, model dilatih dari contoh buatan. Di markas, model belajar dari lalu lintas asli selama 14 hari.
- Kalau ada serangan **selama** masa belajar, serangan itu ikut dianggap normal.
- Kebiasaan markas berubah (misalnya ada perangkat baru). Versi sekarang belum melatih ulang otomatis. Untuk melatih ulang, ulangi masa belajar.
- Tombol "Bukan ancaman" pada kejadian perilaku tidak biasa mematikan peringatan perilaku untuk perangkat itu.

## Bagian B · Asisten piket

### 9. Tanya kotak

Petugas mengetik pertanyaan di kotak "Asisten piket", misalnya *"Ada apa dengan Kamera Gerbang Utama?"*. Yang terjadi di `ShiftAssistant.ask`:

1. **Mencari** (`retrieve`): kata-kata pertanyaan dicocokkan dengan semua kejadian dan perangkat. Kata yang jarang muncul (misalnya "kamera") diberi bobot lebih besar daripada kata umum (misalnya "utama"). Nomor kejadian yang disebut langsung (misalnya "PJS-0003") diutamakan.
2. **Menyusun prompt**: hanya kejadian dan perangkat yang cocok yang dimasukkan sebagai DATA. AI diperintahkan menjawab **hanya** dari DATA, menyebut nomor kejadian sumbernya, dan berkata "Saya tidak menemukan datanya" kalau memang tidak ada.
3. **Memeriksa jawaban**: nomor kejadian yang disebut AI dicocokkan dengan DATA. Nomor yang tidak ada (karangan AI) **dibuang**.
4. **Mencatat**: pertanyaan dan sumbernya ditulis ke catatan bukti (`tanya_kotak`).

Cara "cari dulu, baru minta AI menjawab dari hasil pencarian" disebut **RAG** (*retrieval-augmented generation*). Ini cara umum untuk menekan halusinasi.

Kalau AI tidak tersedia, asisten tetap menjawab dengan hasil pencarian: "Catatan yang paling cocok: PJS-0003 (menunggu keputusan): Kamera Gerbang Utama mengirim data ke luar markas."

### 10. Laporan ganti piket

Tombol "Buat laporan" menyusun laporan untuk 8, 12, atau 24 jam terakhir. Isinya:

- ringkasan,
- daftar semua kejadian beserta statusnya,
- kejadian yang harus ditindaklanjuti piket berikutnya,
- perangkat baru,
- status catatan bukti dan kode buku jaga.

**Daftar dan angka selalu diambil langsung dari data**, tidak pernah ditulis AI. AI hanya menulis paragraf ringkasan 2–4 kalimat. Jadi kalaupun AI salah menulis ringkasan, daftar di bawahnya tetap benar dan bisa dicocokkan.

Laporan bisa disalin dengan tombol "Salin" untuk ditempel ke buku jaga digital atau pesan ke atasan. Pembuatan laporan juga dicatat (`laporan_piket`).

## Latihan

1. Jalankan demo dan tunggu kejadian "Perilaku tidak biasa: Kunci Pintu Gudang Senjata". Baca alasannya. Ciri mana yang paling menonjol?
2. Di Python, latih model dari contoh demo, lalu beri skor kasus buatanmu sendiri:

   ```python
   from pjs import config
   from pjs.anomaly import BehaviorWatcher
   class Kosong:
       def list_samples(self, zone): return []
   cfg = config.load("config.demo.json")
   w = BehaviorWatcher(cfg["anomaly"], Kosong(), cfg.base_dir)
   w.train()
   print(w.evaluate("ot", {"flows": 3, "destinations": 3, "ports": 1, "bytes_out": 2000, "bytes_in": 2000, "external": 0, "hour": 14}))
   ```

   Cari angka terkecil yang membuat kasusmu ditandai.
3. Ubah `threshold` di `config.demo.json` menjadi `0.55`. Apa yang terjadi pada jumlah kejadian? Kenapa ambang terlalu rendah berbahaya?
4. Tanyakan ke asisten: "Apa yang terjadi pada genset?", "Siapa yang menyerang?", dan "Berapa suhu ruangan?". Bandingkan jawabannya. Mana yang seharusnya dijawab "tidak menemukan datanya"?
5. Buka `tests/test_assistant.py`, baca `test_ai_answer_keeps_only_real_sources`. Jelaskan kenapa tes ini penting.

## Kamu paham kalau...

- bisa menjelaskan Isolation Forest dengan gambar titik dan belahan,
- bisa menjelaskan kenapa skor AI tidak langsung memblokir,
- bisa menjelaskan bagaimana asisten mencegah AI mengarang nomor kejadian,
- bisa menjawab pertanyaan juri: "Di mana AI-nya, dan kenapa AI dipakai di situ?"
