# Pembagian kerja tim (3 orang)

Program kotak, dashboard, alat lab, dan tes **sudah tersedia di repositori ini**. Sisa waktu dipakai untuk memahami, memasang di lab, menguji, merapikan, dan menyiapkan **lima berkas pengumpulan**: link karya, thumbnail, screenshot, video, dan slide. Rinciannya ada di [PENGUMPULAN-KARYA.md](PENGUMPULAN-KARYA.md).

| Orang | Peran | Bagian yang dipegang |
|---|---|---|
| A | Jaringan dan keamanan | `aturan/`, `lab/`, `docs/PANDUAN-LAB.md`, lampu genset, screenshot lab, bagian arsitektur dan hasil uji di slide |
| B | Program dan AI | `pjs/`, `tests/`, penjelas AI, langkah SOP, bagian teknologi dan pagar pengaman AI di slide |
| C | Tampilan dan cerita | `web/`, `docs/belajar/`, slide, naskah dan suntingan video, thumbnail, screenshot dashboard, mengirim pengumpulan |

Tentukan sendiri siapa A, B, dan C. Bagian lain boleh disentuh, tetapi beri tahu pemiliknya dulu supaya tidak saling menimpa.

Rulebook mewajibkan **setiap anggota berkontribusi aktif**. Kalau jumlah anggota berubah setelah pendaftaran, ajukan ke panitia paling lambat **Minggu, 8 November**.

## Jadwal

| Tanggal | A · jaringan dan keamanan | B · program dan AI | C · tampilan dan cerita |
|---|---|---|---|
| Sel–Rab, 3–4 Nov | Susun lab virtual (bagian 1–4 [PANDUAN-LAB](PANDUAN-LAB.md)) sampai Suricata menulis peringatan genset | Baca [belajar 08–09](belajar/08-python-untuk-proyek-ini.md), jalankan tes, pasang Ollama, pilih model | Jalankan demo, pesan perlengkapan lampu **hari ini**, baca belajar 10–11, tulis naskah video dan kerangka slide |
| Kam–Sab, 5–7 Nov | **Kamis 5 Nov: Webinar 2 bertiga.** Blokir MikroTik sungguhan, rakit lampu ESP32 kalau barangnya sudah datang | Sambungkan kotak ke Suricata di lab (bersama A), sesuaikan langkah SOP, uji penjelasan AI | Sesuaikan dashboard (nama satuan, tampilan), draf slide, rancang thumbnail |
| Min–Sen, 8–9 Nov | **Minggu 8 Nov: anggota tim harus sudah pasti.** Bertiga: jalankan keempat skenario di lab dari awal sampai akhir. A mencatat masalah di lab | Perbaiki masalah yang ditemukan | Susun alur video, ambil screenshot dashboard |
| Sel–Kam, 10–12 Nov | Bertiga: latihan demo dan rekam video (maksimal 10 menit). A menjalankan lab, B menjaga kotak dan AI, C membawakan cerita. **Kamis 12 Nov berhenti menambah fitur** | | |
| Jum–Sab, 13–14 Nov | Tulis bagian arsitektur, hasil uji lab, dan perkiraan biaya di slide. Ambil screenshot lab | Tulis bagian teknologi dan pagar pengaman AI di slide. Ubah repo jadi publik. Siaga perbaikan | Sunting video dan unggah ke YouTube, buat thumbnail, satukan slide. **Kumpulkan Sabtu 14 Nov** |
| Min, 15 Nov | Cadangan. Batas resmi pukul **23.59 WIB** | | |

## Titik periksa

Kalau satu titik tidak tercapai, potong pekerjaan bonus, jangan geser tanggal pengumpulan.

| Kapan | Harus sudah bisa |
|---|---|
| Rabu 4 Nov | Suricata di lab menulis peringatan "PJS OT perintah tulis Modbus" saat skrip serangan dijalankan |
| Sabtu 7 Nov | Skenario genset utuh di lab: serangan → terdeteksi → MikroTik memblokir → penjelasan muncul → tercatat di catatan bukti |
| Minggu 8 Nov | Jumlah dan nama anggota tim sudah pasti di platform |
| Kamis 12 Nov | Video demo selesai direkam |
| Sabtu 14 Nov | Lima berkas terkumpul (lihat daftar periksa di [PENGUMPULAN-KARYA](PENGUMPULAN-KARYA.md)) |

## Wajib dan bonus

| Wajib jalan saat demo | Bonus kalau waktu cukup |
|---|---|
| Skenario genset di lab dengan blokir MikroTik sungguhan | Lampu ESP32 fisik (tanpa lampu, pakai halaman lampu genset tiruan) |
| Dashboard dengan kartu penjelasan dan tombol | Penjelasan AI (tanpa AI, penjelasan bawaan tetap tampil) |
| Catatan bukti dan pemeriksaannya (skenario 4) | Uji coba di jaringan nyata dengan izin pemiliknya |
| Lima berkas pengumpulan | |
| Skenario kamera dan sinyal berkala di lab sungguhan (dengan 3 orang, ini dikejar; kalau macet, tunjukkan lewat mode demo) | |

## Kalau lolos ke final (24 November)

- Minimal satu orang wajib hadir di Jakarta. Tim finalis yang tidak hadir otomatis gugur.
- Presentasi 10 menit sudah termasuk demo dan tanya jawab. Latih naskahnya di [belajar/11](belajar/11-demo-dan-tanya-jawab.md).

## Kebiasaan kecil

- **Rapat 15 menit setiap malam:** apa yang selesai, apa yang macet.
- **Sebelum mulai kerja:** `git pull`. **Setelah selesai:** `git add`, `git commit`, `git push`.
- **Jangan dua orang mengubah berkas yang sama di waktu yang sama.**
- **Jangan saling menunggu.** B dan C bisa bekerja dengan `python -m pjs demo` tanpa menunggu lab A selesai.
- **Uji hanya di lab sendiri.** Mencoba alat ini ke jaringan orang lain atau milik panitia melanggar kode etik dan bisa didiskualifikasi.
