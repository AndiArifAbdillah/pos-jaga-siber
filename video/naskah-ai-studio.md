# Naskah untuk Google AI Studio (suara AI Gemini)

Naskah video dibagi menjadi 4 bagian. Setiap bagian dibuat suaranya sekali, lalu diunduh.

## Langkah

1. Buka **aistudio.google.com**, lalu pilih halaman pembuat suara (*Generate speech* / *Speech*).
2. Pilih model **Gemini 3.8 Flash TTS**. Kalau model itu menolak karena batas harian, pilih model TTS lain, tapi **pakai model yang sama untuk keempat bagian**.
3. Pilih mode **satu pembicara** (*single speaker*), lalu pilih suara **Charon** atau **Orus**. **Pakai suara yang sama untuk keempat bagian.**
4. Untuk setiap bagian di bawah:
   - Kalau ada kotak *Style instructions*, salin isi **Gaya** ke sana. Kalau tidak ada, lewati.
   - Salin isi **Teks** ke kotak teks, lalu klik **Run**.
   - Setelah suaranya jadi, unduh audionya. Beri nama `bagian-1`, `bagian-2`, dan seterusnya.
5. Kirim keempat berkas ke chat, lalu sebutkan suara yang dipakai.

Teks jangan diubah. Tanda `<short pause>` membuat jeda pendek di antara kalimat, supaya audionya bisa dipotong per kalimat. Kalau tanda itu malah ikut dibacakan, hapus semua tanda itu dan ganti dengan baris kosong.

## Bagian 1 (kalimat 1–13)

**Gaya:**

```
natural, expressive Indonesian documentary narrator, warm and clear. Scene moods in order: slow, hushed and suspenseful, like the cold open of a documentary; then serious and concerned; then confident, bright and reassuring.
```

**Teks:**

```
Pukul dua pagi di sebuah markas. Listrik PLN padam, dan genset seharusnya menyala.
<short pause>
Tapi seseorang di jaringan kantor baru saja mengirim perintah untuk mematikannya.
<short pause>
Tidak ada antivirus yang menjaga genset. Dan petugas jaga bukan ahli siber.
<short pause>
Inilah Pos Jaga Siber.
<short pause>
Markas hari ini punya dua jaringan: komputer kantor, dan peralatan seperti genset, kamera CCTV, dan kunci pintu elektronik.
<short pause>
Peralatan ini tidak bisa dipasangi antivirus, jarang diperbarui, dan bahasanya tidak memakai kata sandi.
<short pause>
Serangan seperti ini sudah terjadi, dari jaringan listrik Ukraina tahun dua ribu lima belas, sampai ratusan ribu kamera yang diambil alih.
<short pause>
Lalu siapa yang menjaga, kalau penjaganya bukan ahli, dan internetnya bisa putus kapan saja?
<short pause>
Pos Jaga Siber adalah kotak penjaga di markas. Ia menerima salinan lalu lintas jaringan, tanpa mengganggu jaringan itu sendiri.
<short pause>
Serangan yang sudah dikenal ditangkap aturan Suricata. Yang belum dikenal, ditangkap Ei-Ai yang mempelajari kebiasaan normal.
<short pause>
Kalau ancamannya kritis dan menyangkut peralatan, kotak langsung memutus pelakunya lewat router MikroTik.
<short pause>
Setiap kejadian dijelaskan Ei-Ai lokal dalam bahasa sehari-hari, lalu dicatat di catatan bukti yang tidak bisa diubah diam-diam.
<short pause>
Semuanya berjalan di dalam kotak: tetap menjaga meskipun internet putus, dan data markas tidak keluar.
```

## Bagian 2 (kalimat 14–23)

**Gaya:**

```
natural, expressive Indonesian documentary narrator, warm and clear. Scene moods in order: relaxed and friendly, like explaining to a friend; then slow and grave; then energetic and urgent, like a live report.
```

**Teks:**

```
Lalu, apa itu Suricata? Suricata adalah program pendeteksi serangan jaringan yang gratis dan terbuka, dikembangkan yayasan O I S F, dan dipakai luas di banyak negara.
<short pause>
Cara kerjanya seperti petugas pemeriksa di pos gerbang: setiap paket data yang lewat dibuka, lalu dicocokkan dengan buku aturan berisi ciri-ciri serangan.
<short pause>
Kalau ada yang cocok, Suricata menulis catatan. Catatan itulah yang dibaca kotak kami untuk memutuskan, memblokir, dan menjelaskan ke petugas.
<short pause>
Tapi Suricata hanya mengenali serangan yang sudah ada aturannya. Karena itu kami menambahkan Ei-Ai untuk menangkap yang belum dikenal.
<short pause>
Di lab kami, genset tiruan memakai bahasa Modbus yang sama dengan panel genset sungguhan.
<short pause>
Satu perintah dari jaringan, tanpa kata sandi apa pun, sudah cukup untuk mematikannya.
<short pause>
Berikut rekaman dashboard aslinya, berjalan di laptop dengan contoh catatan sensor.
<short pause>
Sebuah laptop asing muncul di jaringan kantor, lalu mengirim perintah tulis ke genset utama.
<short pause>
Kejadian ini langsung ditandai kritis, dan laptop itu diisolasi otomatis tanpa menunggu petugas.
<short pause>
Ei-Ai lokal menjelaskan apa yang terjadi, kenapa berbahaya, dan langkah SOP yang bisa dicentang petugas.
```

## Bagian 3 (kalimat 24–33)

**Gaya:**

```
natural, expressive Indonesian documentary narrator, warm and clear. Scene moods in order: calm and clear; then curious and engaging; then warm and friendly.
```

**Teks:**

```
Tidak semua kejadian diblokir otomatis. Kamera gerbang yang mengunggah empat puluh delapan megabita ke luar markas, ditandai tinggi.
<short pause>
Laptop staf yang menghubungi alamat luar dengan jarak waktu sangat teratur, ciri program jahat yang melapor ke pengendalinya, juga ditandai.
<short pause>
Untuk kejadian seperti ini, keputusan tetap di tangan petugas, cukup dengan satu tombol.
<short pause>
Sekarang, serangan yang tidak punya aturan sama sekali. Kunci pintu gudang senjata tiba-tiba menghubungi empat belas perangkat, dalam sepuluh detik.
<short pause>
Di sinilah Ei-Ai deteksi perilaku bekerja. Kotak mempelajari kebiasaan normal setiap jaringan, dengan machine learning bernama Isolation Forest.
<short pause>
Prinsipnya sederhana: yang aneh lebih cepat terpisah dari kerumunan. Perangkat normal butuh banyak belahan, perangkat aneh cukup dua atau tiga.
<short pause>
Hasilnya, skor keanehan satu koma nol, lengkap dengan alasannya. Dan seperti semua temuan Ei-Ai, keputusan tetap di tangan petugas.
<short pause>
Ei-Ai ketiga adalah asisten piket. Petugas cukup bertanya dengan bahasa sehari-hari.
<short pause>
Asisten mencari di catatan kotak dulu, lalu menjawab hanya dari data itu, lengkap dengan nomor kejadian sumbernya.
<short pause>
Kalau datanya tidak ada, ia mengaku tidak tahu. Dan di akhir piket, laporan ganti piket tersusun dengan satu tombol.
```

## Bagian 4 (kalimat 34–41)

**Gaya:**

```
natural, expressive Indonesian documentary narrator, warm and clear. Scene moods in order: serious and firm; then firm and reassuring; then proud, warm and confident; slow down on the final sentence.
```

**Teks:**

```
Setiap kejadian dan tindakan petugas disimpan seperti rantai: setiap entri mengunci sidik jari entri sebelumnya, dan ditandatangani kotak.
<short pause>
Kalau satu entri saja dihapus untuk menghilangkan jejak, rantainya putus, dan kotak langsung menunjukkan entri mana yang hilang.
<short pause>
Kode pendek di layar disalin ke buku jaga kertas setiap ganti piket, menjadi saksi yang tidak bisa dihapus dari jauh.
<short pause>
Prinsip kami: Ei-Ai menemukan dan menjelaskan, sedangkan aturan tetap dan manusia yang memutuskan. Tidak ada Ei-Ai yang bisa memblokir.
<short pause>
Blokir otomatis hanya untuk kejadian kritis pada peralatan, berlaku dua puluh empat jam, dan tidak pernah menyentuh router atau kotak itu sendiri.
<short pause>
Perangkat lunaknya bebas biaya lisensi. Kotaknya cukup satu mini PC dengan dua colokan jaringan, ditambah router MikroTik yang umumnya sudah ada di markas.
<short pause>
Purwarupa ini lulus empat puluh satu tes otomatis, dan seluruh kode serta dokumentasinya terbuka untuk dewan juri.
<short pause>
Pos Jaga Siber. Penjaga jaringan markas yang bekerja mandiri, menjelaskan ancaman dalam bahasa sehari-hari, dan langsung mengamankan peralatan penting.
```
