# Pembagian kerja tim (3 orang)

Program kotak, dashboard, alat lab, dan tes **sudah tersedia di repositori ini**. Sisa waktu dipakai untuk memahami, memasang di lab, menguji, merapikan, dan membuat video serta proposal.

| Orang | Peran | Bagian repositori yang dipegang |
|---|---|---|
| A | Jaringan dan keamanan | `aturan/`, `lab/`, `docs/PANDUAN-LAB.md` |
| B | Program dan AI | `pjs/`, `tests/` |
| C | Tampilan dan cerita | `web/`, `docs/`, video, proposal |

Bagian lain boleh disentuh, tetapi beri tahu pemiliknya dulu supaya tidak saling menimpa.

## Jadwal

| Tanggal | A · jaringan | B · program dan AI | C · tampilan dan cerita |
|---|---|---|---|
| Sen–Rab, 2–4 Nov | Susun lab virtual (bagian 1–4 [PANDUAN-LAB](PANDUAN-LAB.md)) sampai Suricata menulis peringatan genset | Baca [belajar 08–09](belajar/08-python-untuk-proyek-ini.md), jalankan tes, pasang Ollama, pilih model | Jalankan demo di laptop, pesan perlengkapan lampu **hari ini**, tulis naskah demo dan kerangka proposal |
| Kam–Sab, 5–7 Nov | Blokir MikroTik sungguhan, rakit lampu ESP32 | Sambungkan kotak ke Suricata di lab, sesuaikan langkah SOP, uji penjelasan AI | Sesuaikan dashboard (nama satuan, tampilan), mulai draf proposal |
| Min–Sen, 8–9 Nov | Bertiga: jalankan keempat skenario di lab dari awal sampai akhir, catat semua masalah | Perbaiki masalah yang ditemukan | Susun alur video (storyboard) |
| Sel–Kam, 10–12 Nov | Bertiga: latihan demo berkali-kali dan rekam video. **Kamis 12 Nov berhenti menambah fitur** | | |
| Jum–Sab, 13–14 Nov | Siaga perbaikan | Siaga perbaikan | Selesaikan proposal dan video, **kumpulkan Sabtu 14 Nov** (sehari sebelum batas) |

## Titik periksa

Kalau satu titik tidak tercapai, potong pekerjaan bonus, jangan geser tanggal pengumpulan.

| Kapan | Harus sudah bisa |
|---|---|
| Rabu 4 Nov | Suricata di lab menulis peringatan "PJS OT perintah tulis Modbus" saat skrip serangan dijalankan |
| Sabtu 7 Nov | Skenario genset utuh di lab: serangan → terdeteksi → MikroTik memblokir → penjelasan muncul → tercatat di catatan bukti |
| Kamis 12 Nov | Video demo selesai direkam |

## Wajib dan bonus

| Wajib jalan saat demo | Bonus kalau waktu cukup |
|---|---|
| Skenario genset dengan blokir MikroTik sungguhan | Lampu ESP32 fisik |
| Dashboard dengan kartu penjelasan dan tombol | Penjelasan AI (tanpa AI, penjelasan bawaan tetap tampil) |
| Catatan bukti dan pemeriksaannya | Skenario kamera dan sinyal berkala di lab sungguhan (sudah ada di demo) |
| Video dan proposal | Uji coba di jaringan nyata dengan izin pemiliknya |

## Kebiasaan kecil

- **Rapat 15 menit setiap malam:** apa yang selesai, apa yang macet.
- **Sebelum mulai kerja:** `git pull`. **Setelah selesai:** `git add`, `git commit`, `git push`.
- **Jangan dua orang mengubah berkas yang sama di waktu yang sama.**
- **Jangan menunggu orang lain.** B dan C bisa bekerja dengan `python -m pjs demo` tanpa menunggu lab A selesai.
