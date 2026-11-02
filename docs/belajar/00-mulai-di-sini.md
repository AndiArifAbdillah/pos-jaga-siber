# Belajar Pos Jaga Siber dari nol

Dokumen ini ditulis untuk orang yang **belum pernah belajar jaringan atau keamanan siber**. Tujuannya, setelah selesai, kamu bisa:

- menjelaskan cara kerja kotak ini ke juri dengan bahasa sendiri,
- membaca dan mengubah setiap berkas di repositori,
- memasang kotak di lab dan memperbaikinya kalau ada yang macet,
- menjawab pertanyaan sulit tentang batas dan kelemahannya.

## Urutan bab

| Bab | Judul | Isi singkat | Perkiraan waktu |
|---|---|---|---|
| 01 | [Jaringan dasar](01-jaringan-dasar.md) | Alamat IP, MAC, port, paket, router, switch | 2 jam |
| 02 | [IT, OT, dan Modbus](02-it-ot-dan-modbus.md) | Bedanya komputer kantor dan peralatan, bahasa yang dipakai genset | 1,5 jam |
| 03 | [Ancaman dan pertahanan](03-ancaman-dan-pertahanan.md) | Serangan yang dijaga kotak ini, cara kerja penjaga pasif | 1,5 jam |
| 04 | [Suricata](04-suricata.md) | "Mata" kotak: membaca paket dan mencocokkan aturan | 2 jam |
| 05 | [MikroTik dan blokir](05-mikrotik-dan-blokir.md) | "Tangan" kotak: mengisolasi perangkat lewat router | 1,5 jam |
| 06 | [AI lokal](06-ai-lokal.md) | "Mulut" kotak: menjelaskan dengan bahasa sehari-hari | 1 jam |
| 07 | [Catatan bukti](07-catatan-bukti.md) | "Buku jaga digital" yang tidak bisa diubah diam-diam | 2 jam |
| 08 | [Python untuk proyek ini](08-python-untuk-proyek-ini.md) | Bagian Python yang dipakai di kode | 2 jam |
| 09 | [Tur kode](09-tur-kode.md) | Perjalanan satu serangan dari paket sampai layar | 2,5 jam |
| 10 | [Dashboard web](10-dashboard-web.md) | HTML, CSS, JavaScript di layar operator | 1,5 jam |
| 11 | [Demo dan tanya jawab](11-demo-dan-tanya-jawab.md) | Naskah demo dan jawaban untuk pertanyaan juri | 1 jam |
| 12 | [Kamus istilah](12-kamus-istilah.md) | Semua istilah dalam satu tempat | (rujukan) |

## Jalur per orang

Semua orang wajib membaca **00, 01, 09 bagian "Perjalanan satu serangan", dan 11**. Selebihnya:

| Orang | Fokus | Bab utama |
|---|---|---|
| A · jaringan dan keamanan | Lab, Suricata, MikroTik | 02, 03, 04, 05, lalu [PANDUAN-LAB](../PANDUAN-LAB.md) |
| B · program dan AI | Kode Python, AI, catatan bukti | 06, 07, 08, 09 lengkap |
| C · tampilan dan cerita | Dashboard, video, proposal | 02, 03, 07 (bagian awal), 10 |

## Cara belajar yang disarankan

1. **Jalankan dulu, baca kemudian.** Sebelum membaca apa pun, jalankan demo:

   ```bash
   python -m pjs demo --putar --baru
   ```

   Buka http://localhost:8080 dan lihat apa yang terjadi. Setiap bab akan menjelaskan satu bagian dari yang kamu lihat.

2. **Kerjakan latihan di akhir bab.** Setiap bab punya latihan kecil. Jangan dilewati: pemahaman datang dari mencoba.

3. **Cek dirimu sendiri.** Setiap bab diakhiri pertanyaan "Kamu paham kalau...". Kalau belum bisa menjawab, baca ulang atau tanya teman satu tim.

4. **Tulis pertanyaanmu.** Simpan daftar hal yang belum paham. Bahas di rapat malam.

## Gambaran besar dalam satu paragraf

Markas punya dua jaringan: **jaringan kantor** (laptop, server) dan **jaringan peralatan** (genset, kamera, kunci pintu). Kotak Pos Jaga mendapat **salinan** semua lalu lintas di kedua jaringan. Program **Suricata** di dalam kotak membaca salinan itu dan menulis catatan ke berkas `eve.json`. Program **pjs** (buatan kita) membaca catatan itu, mengenali perangkat, dan memutuskan mana yang berbahaya. Kalau kritis dan menyangkut peralatan, pjs menyuruh **router MikroTik** mengisolasi pelakunya. Setiap kejadian dijelaskan dalam bahasa sehari-hari oleh **AI lokal**, lalu ditampilkan di **dashboard** untuk petugas jaga. Semua kejadian dan tindakan ditulis di **catatan bukti** yang bersambung seperti rantai, sehingga tidak bisa diubah diam-diam.

```
salinan lalu lintas ──► Suricata ──► eve.json ──► pjs ──┬──► MikroTik (isolasi)
                        (mata)                   (otak) ├──► AI lokal (penjelasan)
                                                        ├──► catatan bukti
                                                        └──► dashboard (layar petugas)
```
