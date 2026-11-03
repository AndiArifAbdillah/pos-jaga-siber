# Pembagian kerja tim (2 orang)

Program kotak, dashboard, alat lab, dan tes **sudah tersedia di repositori ini**. Sisa waktu dipakai untuk memahami, memasang di lab, menguji, merapikan, dan menyiapkan **lima berkas pengumpulan**: link karya, thumbnail, screenshot, video, dan slide. Rinciannya ada di [PENGUMPULAN-KARYA.md](PENGUMPULAN-KARYA.md).

| Orang | Peran | Bagian yang dipegang |
|---|---|---|
| A | Jaringan, lab, dan perangkat | `aturan/`, `lab/`, `docs/PANDUAN-LAB.md`, bagian teknis slide, screenshot lab |
| B | Program, AI, tampilan, dan cerita | `pjs/`, `web/`, `tests/`, `docs/belajar/`, slide, video, thumbnail, screenshot dashboard |

Bagian lain boleh disentuh, tetapi beri tahu pasanganmu dulu supaya tidak saling menimpa.

Rulebook mewajibkan **setiap anggota berkontribusi aktif**. Kalau jumlah anggota berubah, ajukan ke panitia paling lambat **Minggu, 8 November**.

## Jadwal

| Tanggal | A · jaringan, lab, perangkat | B · program, AI, tampilan, cerita |
|---|---|---|
| Sel–Rab, 3–4 Nov | Susun lab virtual (bagian 1–4 [PANDUAN-LAB](PANDUAN-LAB.md)) sampai Suricata menulis peringatan genset | Jalankan demo, baca [belajar 08–10](belajar/08-python-untuk-proyek-ini.md), pasang Ollama. Pesan perlengkapan lampu **hari ini**. Tulis kerangka slide dan naskah video |
| Kam–Sab, 5–7 Nov | **Kamis 5 Nov: ikuti Webinar 2 berdua.** Blokir MikroTik sungguhan. Sambungkan kotak ke Suricata di lab (bersama B). Rakit lampu ESP32 kalau barangnya sudah datang | **Kamis 5 Nov: ikuti Webinar 2 berdua.** Uji penjelasan AI dan pilih model. Sesuaikan langkah SOP dan nama satuan di dashboard. Draf slide |
| Min–Sen, 8–9 Nov | **Minggu 8 Nov: jumlah anggota tim harus sudah pasti.** Berdua: jalankan skenario di lab dari awal sampai akhir, catat semua masalah | Berdua: perbaiki masalah yang ditemukan, susun alur video |
| Sel–Kam, 10–12 Nov | Berdua: latihan demo dan rekam video (maksimal 10 menit). A menjalankan lab, B membawakan cerita. **Kamis 12 Nov berhenti menambah fitur** | |
| Jum–Sab, 13–14 Nov | Tulis bagian teknis slide (arsitektur, hasil uji lab, perkiraan biaya). Ambil screenshot lab. Siaga perbaikan | Sunting video dan unggah ke YouTube. Ambil screenshot dashboard, buat thumbnail, satukan slide. Ubah repo jadi publik. **Kumpulkan Sabtu 14 Nov** |
| Min, 15 Nov | Cadangan. Batas resmi pukul **23.59 WIB** | |

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

Dengan 2 orang, fokus pada skenario genset. Skenario lain cukup ditunjukkan lewat mode demo kalau waktu tidak cukup.

| Wajib jalan saat demo | Bonus kalau waktu cukup |
|---|---|
| Skenario genset di lab dengan blokir MikroTik sungguhan | Lampu ESP32 fisik (tanpa lampu, pakai halaman lampu genset tiruan) |
| Dashboard dengan kartu penjelasan dan tombol | Penjelasan AI (tanpa AI, penjelasan bawaan tetap tampil) |
| Catatan bukti dan pemeriksaannya (skenario 4) | Skenario kamera dan sinyal berkala di lab sungguhan (sudah ada di mode demo) |
| Lima berkas pengumpulan | Uji coba di jaringan nyata dengan izin pemiliknya |

## Kalau lolos ke final (24 November)

- Minimal satu orang wajib hadir di Jakarta. Tim finalis yang tidak hadir otomatis gugur.
- Presentasi 10 menit sudah termasuk demo dan tanya jawab. Latih naskahnya di [belajar/11](belajar/11-demo-dan-tanya-jawab.md).

## Kebiasaan kecil

- **Rapat 15 menit setiap malam:** apa yang selesai, apa yang macet.
- **Sebelum mulai kerja:** `git pull`. **Setelah selesai:** `git add`, `git commit`, `git push`.
- **Jangan mengubah berkas yang sama di waktu yang sama.**
- **Jangan saling menunggu.** B bisa bekerja dengan `python -m pjs demo` tanpa menunggu lab A selesai.
- **Uji hanya di lab sendiri.** Mencoba alat ini ke jaringan orang lain atau milik panitia melanggar kode etik dan bisa didiskualifikasi.
