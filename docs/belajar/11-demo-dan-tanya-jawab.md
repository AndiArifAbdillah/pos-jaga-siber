# 11 · Demo dan tanya jawab

## 1. Kalimat inti

Pakai kalimat yang sama di slide, video, dan presentasi:

> **Pos Jaga Siber adalah penjaga jaringan markas yang bekerja mandiri, menjelaskan ancaman dalam bahasa sehari-hari, dan langsung mengamankan peralatan penting seperti genset dan kamera.**

Hindari kata "offline". Pakai **"mandiri: tetap menjaga meskipun internet putus, dan data markas tidak keluar"**.

## 2. Dua kali tampil, dua aturan waktu

| | Video (babak penyisihan) | Presentasi final (24 November) |
|---|---|---|
| Batas waktu | Maksimal **10 menit**, diunggah ke YouTube | **10 menit sudah termasuk** penjelasan, demo, **dan tanya jawab** |
| Penonton | Juri menonton sendiri, bisa diulang | Juri di depan kalian, bertanya langsung |
| Isi | Keempat skenario lengkap | Skenario genset dan catatan bukti saja. Skenario lain cukup disebut |

Alur video ada di [PENGUMPULAN-KARYA.md](../PENGUMPULAN-KARYA.md). Alur presentasi final:

| Menit | Isi | Yang ditunjukkan |
|---|---|---|
| 0:00 | **Masalah.** Markas punya genset, kamera, dan kunci pintu yang tersambung jaringan. Peralatan ini tidak bisa dipasangi antivirus. Petugas jaga bukan ahli siber | Foto/gambar markas, daftar peralatan |
| 1:00 | **Solusi.** Kalimat inti dan gambar cara kerja | Slide cara kerja |
| 1:30 | **Demo skenario 1.** Laptop asing mencoba mematikan genset | Lampu genset, dashboard, MikroTik |
| 3:30 | **Demo skenario 5 dan asisten.** AI deteksi perilaku menangkap kunci pintu yang memindai jaringan, lalu tanya asisten satu pertanyaan | Skor keanehan dan alasannya, jawaban asisten dengan nomor kejadian |
| 4:45 | **Demo skenario 4 singkat.** Catatan bukti diubah, lalu ketahuan | Layar merah, kode buku jaga |
| 5:15 | **Pembeda.** Tiga cara AI dipakai, mandiri, peralatan dipisah, catatan bukti | Slide pembeda |
| 5:45 | **Kelayakan dan penutup** dengan kalimat inti | Biaya per kotak, hasil uji lab, rencana pemasangan bertahap |
| 6:30 | **Tanya jawab** (sekitar 3,5 menit) | Tabel di bagian 5 |

Kalau waktu tanya jawab terpotong, juri tidak sempat melihat kekuatan kalian. Latih bagian 0:00–6:30 sampai **tidak lebih dari 6,5 menit**.

## 3. Naskah demo

### Skenario 1: genset (yang paling penting, latih paling sering)

1. Tunjukkan lampu genset menyala dan dashboard dalam keadaan tenang.
2. *"Ini laptop yang dibawa tamu dan dicolokkan ke jaringan kantor."* Jalankan `serangan_genset.py --ulang 5`.
3. Dashboard: muncul "Ada perangkat baru di jaringan", lalu **"Perintah asing ke Genset utama", KRITIS, diisolasi otomatis**.
4. *"Kotak tidak menunggu petugas. Untuk genset, satu detik terlambat bisa berarti listrik padam."* Tunjukkan kiriman berikutnya di terminal penyerang **GAGAL**.
5. Tunjukkan di MikroTik: `/ip firewall address-list print`. Alamat laptop ada di `pjs-karantina`, sisa 24 jam.
6. Klik kejadian. Bacakan "Apa yang terjadi" dan "Kenapa berbahaya". *"Petugas tidak perlu tahu apa itu Modbus."*
7. Centang langkah pertama. Tunjukkan entri baru di catatan bukti.

Kalau lampu ESP32 belum siap, tunjukkan halaman lampu genset tiruan di browser.

### Skenario 2: kamera mengirim ke luar

*"Kamera murah sering diam-diam mengirim rekaman ke server pabriknya."* Kejadian muncul dengan tingkat tinggi. Kotak **tidak** memblokir sendiri. Petugas yang menekan **Isolasi perangkat**. *"Untuk kejadian yang tidak kritis, keputusan tetap di tangan manusia."*

### Skenario 3: sinyal berkala

*"Laptop staf ini terlihat normal, tetapi setiap 10 detik menghubungi alamat yang sama di luar. Itu ciri program jahat yang menunggu perintah."* Tunjukkan "jarak rata-rata ... detik" di rincian.

### Skenario 4: catatan diubah

*"Misalkan ada yang ingin menghapus jejak."* Jalankan `ubah_catatan.py`, tekan **Periksa sekarang**. Layar merah: "Entri #… hilang". *"Dan kode di buku jaga kertas tidak bisa dihapus dari jauh."*

### Skenario 5: AI deteksi perilaku (wajib, karena tema lomba adalah AI)

*"Tiga skenario tadi tertangkap aturan. Sekarang serangan yang tidak ada aturannya."* Kunci pintu gudang senjata, yang biasanya hanya berbicara dengan PC pengendali, tiba-tiba menghubungi 14 alamat dalam 10 detik (di lab: `pindai_tiruan.py`).

Klik kejadian "Perilaku tidak biasa". Tunjukkan kotak biru **AI deteksi perilaku**: skor keanehan dan alasannya. *"AI ini mempelajari kebiasaan normal setiap jaringan dengan machine learning. Ia tidak tahu nama serangannya, tetapi tahu ini tidak biasa, dan menjelaskan kenapa."*

Tekankan: *"Temuan AI tidak memblokir sendiri. Keputusan tetap di tangan petugas."*

### Asisten piket

Ketik di kotak Asisten piket: *"Ada apa dengan Kamera Gerbang Utama?"* Tunjukkan jawabannya dan tombol nomor kejadian sumbernya. *"AI hanya menjawab dari catatan kotak. Nomor kejadian yang tidak ada di catatan dibuang."* Lalu tekan **Buat laporan**: laporan ganti piket siap disalin ke buku jaga.

## 4. Daftar periksa sebelum demo

- [ ] Semua VM menyala, jam VM sesuai.
- [ ] `sudo suricata -T` lulus, `eve.json` bertambah.
- [ ] `python3 -m pjs uji-mikrotik` berhasil.
- [ ] Daftar `pjs-karantina` di MikroTik **kosong** sebelum mulai.
- [ ] Genset tiruan menyala (lampu menyala).
- [ ] Data kotak bersih: hentikan kotak, kosongkan folder data, jalankan lagi.
- [ ] Nama operator diisi.
- [ ] Ollama sudah "dipanaskan" (`uji-ai` sekali), supaya jawaban pertama tidak lambat.
- [ ] Rekaman video cadangan siap, kalau demo langsung gagal.

## 5. Pertanyaan juri dan jawabannya

| Pertanyaan | Jawaban |
|---|---|
| "Di mana AI-nya?" | Di tiga tempat. (1) AI deteksi perilaku: machine learning (Isolation Forest) yang mempelajari kebiasaan normal dan menemukan perangkat yang berubah perilaku, termasuk serangan yang belum punya aturan. (2) Penjelas: model bahasa lokal menjelaskan setiap kejadian ke petugas. (3) Asisten piket: menjawab pertanyaan dan menyusun laporan ganti piket dari data kotak. Semuanya berjalan di dalam kotak |
| "Kenapa tidak semua deteksi memakai AI?" | Untuk genset, aturan tetap lebih bisa dipertanggungjawabkan: hasilnya pasti dan bisa diperiksa ulang. AI dipakai di tempat yang tidak bisa ditangani aturan, yaitu hal yang belum dikenal dan bahasa manusia. Itu yang kami maksud "tepat guna" |
| "Model machine learning-nya dilatih pakai data apa?" | Di markas, dari lalu lintas markas itu sendiri selama masa belajar 14 hari, karena setiap markas punya kebiasaan berbeda. Untuk demo, dari 800 contoh perilaku normal buatan. Dari 800 contoh normal itu, tidak ada satu pun yang salah ditandai |
| "Kenapa Isolation Forest, bukan deep learning?" | Tidak butuh data serangan berlabel (yang memang tidak dimiliki markas), cukup data normal. Ringan, berjalan di mini PC tanpa kartu grafis, dan alasannya bisa dijelaskan ke petugas |
| "Bagaimana AI tidak mengarang jawaban?" | Asisten mencari data dulu, lalu AI hanya boleh menjawab dari data itu. Nomor kejadian yang disebut AI dicek, yang tidak ada dibuang. Di laporan piket, daftar kejadian dan angka diambil langsung dari data, AI hanya menulis ringkasannya |
| "Ini kan cuma Suricata ditambah AI?" | Suricata hanya "mata". Yang kami bangun adalah apa yang terjadi setelahnya: pengenalan peralatan OT, keputusan otomatis yang aman untuk genset, penjelasan untuk petugas non-ahli, dan catatan bukti. Produk serupa dibuat untuk analis ahli di ruang kendali. Ini dibuat untuk petugas jaga di markas |
| "Kenapa tidak pakai produk komersial?" | Produk komersial umumnya butuh langganan dan internet, serta mengirim data ke luar negeri. Kotak ini mandiri, berbahasa Indonesia, dan bisa dirawat sendiri |
| "Kenapa offline? Serangan kan dari internet?" | Kotak tetap mengawasi lalu lintas internet. "Mandiri" artinya kotak tidak butuh internet untuk bekerja. Penyerang sering memutus internet lebih dulu, banyak serangan datang dari dalam (flashdisk, laptop tamu), dan data militer tidak boleh keluar |
| "Bagaimana kalau AI salah?" | AI hanya menjelaskan. AI tidak bisa memblokir dan tidak menulis langkah. Langkah dari SOP, blokir dari aturan tetap. Kalau AI mati, penjelasan bawaan tetap tampil |
| "Bagaimana kalau salah blokir?" | Blokir otomatis hanya untuk kejadian kritis pada peralatan. Router, kotak, dan pengendali resmi tidak pernah diblokir. Blokir punya batas waktu 24 jam dan bisa dibatalkan dengan satu tombol. Semuanya tercatat |
| "Bagaimana dengan alarm palsu?" | Ada masa belajar 14 hari dan tombol "Bukan ancaman" yang membuat kejadian serupa tidak dibunyikan lagi. Tombol itu juga tercatat |
| "Ini blockchain?" | Memakai prinsip inti blockchain: rantai hash dan tanda tangan digital, ditambah saksi di luar kotak (kode buku jaga). Tanpa konsensus, karena hanya satu penulis. Lebih ringan dan tetap jalan tanpa jaringan |
| "Bagaimana kalau kotaknya dicuri atau dimatikan?" | Kalau kotak mati, jaringan tetap berjalan, karena kotak hanya menerima salinan. Kode buku jaga dan sinkron ke pusat menjadi saksi yang tidak ikut hilang. Versi lanjut memakai chip TPM untuk kunci |
| "Bagaimana kalau lalu lintasnya terenkripsi?" | Kotak tidak membaca isi, hanya metadata: siapa ke siapa, kapan, berapa banyak, nama tujuan. Itu cukup untuk aturan peralatan ke luar dan sinyal berkala. Modbus sendiri tidak terenkripsi |
| "Sudah diuji di jaringan nyata?" | Jawab jujur sesuai keadaan. Sampai saat ini baru di lab virtual dengan Suricata dan MikroTik sungguhan. Sebutkan angka hasil uji lab |
| "Berapa biayanya per markas?" | Siapkan angka: mini PC dengan dua kartu jaringan, ditambah switch yang bisa port mirror kalau router tidak bisa menyalin lalu lintas. Perangkat lunaknya gratis semua |
| "Bagaimana memperbarui aturan tanpa internet?" | Aturan dikirim dari pusat saat kotak tersambung, atau dibawa dengan media yang sudah diperiksa. Aturan khusus peralatan jarang berubah |
| "Kenapa hanya Modbus?" | Modbus paling umum untuk genset dan panel listrik. Suricata juga memahami DNP3 dan ENIP. Menambah jenis kejadian baru cukup lewat aturan dan playbook, tanpa mengubah kode lain |

## 6. Hal yang jangan dikatakan

- "Tidak bisa diretas." Tidak ada sistem yang tidak bisa diretas.
- "AI-nya memutuskan." AI tidak memutuskan apa pun.
- "AI-nya pasti benar" atau "akurasinya 100%". Sebut angka yang benar-benar diuji, dan sebut bahwa data demo adalah data buatan.
- "Blockchain" tanpa penjelasan.
- Klaim uji coba yang belum dilakukan.

## Latihan

1. Latih skenario 1 sampai bisa selesai di bawah 90 detik tanpa melihat catatan.
2. Minta teman satu tim menjadi juri dan mengajukan 5 pertanyaan acak dari tabel di atas.
3. Tulis jawabanmu sendiri untuk pertanyaan "Apa yang terjadi kalau penyerang memakai alamat IP pengendali resmi?". Petunjuk: MAC, perangkat baru, dan batas aturan berbasis alamat.
