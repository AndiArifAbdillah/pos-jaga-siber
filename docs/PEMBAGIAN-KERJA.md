# Pembagian kerja tim (2 orang)

Program kotak, dashboard, alat lab, dan tes **sudah tersedia di repositori ini**. Sisa waktu dipakai untuk memahami, memasang di lab, menguji, merapikan, dan membuat video serta proposal.

| Orang | Peran | Bagian repositori yang dipegang |
|---|---|---|
| A | Jaringan, lab, dan perangkat | `aturan/`, `lab/`, `docs/PANDUAN-LAB.md` |
| B | Program, AI, tampilan, dan cerita | `pjs/`, `web/`, `tests/`, `docs/belajar/`, proposal, video |

Bagian lain boleh disentuh, tetapi beri tahu pasanganmu dulu supaya tidak saling menimpa.

## Jadwal

| Tanggal | A · jaringan, lab, perangkat | B · program, AI, tampilan, cerita |
|---|---|---|
| Sel–Rab, 3–4 Nov | Susun lab virtual (bagian 1–4 [PANDUAN-LAB](PANDUAN-LAB.md)) sampai Suricata menulis peringatan genset | Jalankan demo, baca [belajar 08–10](belajar/08-python-untuk-proyek-ini.md), pasang Ollama. Pesan perlengkapan lampu **hari ini**. Tulis kerangka proposal dan naskah demo |
| Kam–Sab, 5–7 Nov | Blokir MikroTik sungguhan. Sambungkan kotak ke Suricata di lab (bersama B). Rakit lampu ESP32 kalau barangnya sudah datang | Uji penjelasan AI dan pilih model. Sesuaikan langkah SOP dan nama satuan di dashboard. Draf proposal |
| Min–Sen, 8–9 Nov | Berdua: jalankan skenario di lab dari awal sampai akhir, catat semua masalah | Berdua: perbaiki masalah yang ditemukan, susun alur video |
| Sel–Kam, 10–12 Nov | Berdua: latihan demo berkali-kali dan rekam video. A menjalankan lab, B membawakan cerita. **Kamis 12 Nov berhenti menambah fitur** | |
| Jum–Sab, 13–14 Nov | Tulis bagian teknis proposal (arsitektur, hasil uji lab, perkiraan biaya). Siaga perbaikan | Sunting video, satukan proposal, **kumpulkan Sabtu 14 Nov** (sehari sebelum batas) |

## Titik periksa

Kalau satu titik tidak tercapai, potong pekerjaan bonus, jangan geser tanggal pengumpulan.

| Kapan | Harus sudah bisa |
|---|---|
| Rabu 4 Nov | Suricata di lab menulis peringatan "PJS OT perintah tulis Modbus" saat skrip serangan dijalankan |
| Sabtu 7 Nov | Skenario genset utuh di lab: serangan → terdeteksi → MikroTik memblokir → penjelasan muncul → tercatat di catatan bukti |
| Kamis 12 Nov | Video demo selesai direkam |

## Wajib dan bonus

Dengan 2 orang, fokus pada skenario genset. Skenario lain cukup ditunjukkan lewat mode demo kalau waktu tidak cukup.

| Wajib jalan saat demo | Bonus kalau waktu cukup |
|---|---|
| Skenario genset di lab dengan blokir MikroTik sungguhan | Lampu ESP32 fisik (tanpa lampu, pakai halaman lampu genset tiruan) |
| Dashboard dengan kartu penjelasan dan tombol | Penjelasan AI (tanpa AI, penjelasan bawaan tetap tampil) |
| Catatan bukti dan pemeriksaannya (skenario 4) | Skenario kamera dan sinyal berkala di lab sungguhan (sudah ada di mode demo) |
| Video dan proposal | Uji coba di jaringan nyata dengan izin pemiliknya |

## Kebiasaan kecil

- **Rapat 15 menit setiap malam:** apa yang selesai, apa yang macet.
- **Sebelum mulai kerja:** `git pull`. **Setelah selesai:** `git add`, `git commit`, `git push`.
- **Jangan mengubah berkas yang sama di waktu yang sama.**
- **Jangan saling menunggu.** B bisa bekerja dengan `python -m pjs demo` tanpa menunggu lab A selesai.
