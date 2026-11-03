# Pengumpulan karya

Disusun dari Rulebook Kartika Cyber Hackathon 2026 (bagian D, G, H, I). Kalau ada perbedaan, yang berlaku adalah rulebook dan pengumuman resmi di kartikacyberhackathon.id.

- **Batas akhir: Minggu, 15 November 2026 pukul 23.59 WIB.** Kiriman yang terlambat tidak diproses dalam keadaan apa pun.
- **Target tim: Sabtu, 14 November**, supaya ada cadangan waktu kalau situs lambat atau ada berkas yang ditolak.
- Dikirim lewat platform: codepolitan.com/dashboard/kartika-cyber-hackathon-2026
- Hanya **1 pengumpulan** per tim. Boleh diperbarui sebelum batas akhir, dan yang dinilai hanya kiriman terakhir.

## Tanggal penting

| Tanggal | Kegiatan |
|---|---|
| Kamis, 5 Nov | Webinar Pembekalan 2 (tidak wajib, sangat dianjurkan; rekamannya tersedia) |
| **Minggu, 8 Nov** | **Batas pengajuan perubahan anggota tim** (butuh persetujuan tertulis panitia, paling lambat 7 hari sebelum batas akhir) |
| Kamis, 12 Nov | Tim berhenti menambah fitur |
| Sabtu, 14 Nov | Target tim mengumpulkan |
| **Minggu, 15 Nov, 23.59 WIB** | **Batas akhir pengumpulan** |
| Senin, 16 Nov | Penjurian online dimulai |
| Jumat, 20 Nov | Pengumuman 10 tim finalis |
| Selasa, 24 Nov | Final di Hotel Aston Kartika, Jakarta |

## Lima berkas wajib

| No | Berkas | Ketentuan rulebook | Penanggung jawab |
|---|---|---|---|
| 1 | Link karya | Link **publik** yang bisa dibuka dan dicoba Dewan Juri | B |
| 2 | Thumbnail | 1200 × 630 px, JPG/PNG/WebP, maksimal 500 KB | B |
| 3 | Screenshot | Tangkapan layar tampilan karya, maksimal 5 gambar | B (1–4), A (5) |
| 4 | Video | Menjelaskan karya, manfaat, dan cara kerjanya. Maksimal 10 menit, diunggah ke YouTube | A menjalankan lab, B membawakan dan menyunting |
| 5 | Slide penjelasan | Fitur, arsitektur, teknologi yang dipakai, dan penjelasan umum karya | B, bagian teknis oleh A |

### 1. Link karya

Pakai link repositori GitHub: `https://github.com/AndiArifAbdillah/pos-jaga-siber`

- [ ] **Ubah repositori menjadi publik** sebelum mengumpulkan. Di GitHub: Settings → General → Danger Zone → Change visibility → Public. Repositori privat tampil "404" bagi juri.
- [ ] Buka link di jendela penyamaran (incognito) untuk memastikan bisa dibuka tanpa masuk akun.
- [ ] Unduh ulang ke folder baru, lalu jalankan `python -m pjs demo --putar --baru`. Pastikan dashboard tampil.
- [ ] Jalankan tes: `python -m unittest discover -s tests -t .` harus berakhir `OK`.

README sudah berisi cara mencoba dalam satu perintah, jadi juri bisa mencobanya tanpa alat apa pun.

### 2. Thumbnail

Isi yang disarankan: nama **Pos Jaga Siber**, kalimat inti, dan potongan dashboard dengan kejadian kritis. Periksa ukuran berkas setelah disimpan (maksimal 500 KB). Simpan sebagai JPG kalau PNG terlalu besar.

### 3. Screenshot (maksimal 5)

Usulan urutan:

1. Dashboard lengkap: kejadian kritis "Perintah asing ke Genset utama" sudah diisolasi otomatis.
2. Rincian kejadian: kartu "Apa yang terjadi", "Kenapa berbahaya", dan langkah SOP yang dicentang.
3. Layar merah "Catatan bukti rusak" setelah skenario 4.
4. Laporan kejadian siap cetak.
5. Lab: terminal penyerang yang gagal setelah diblokir, berdampingan dengan daftar `pjs-karantina` di MikroTik (atau lampu genset).

### 4. Video (maksimal 10 menit, YouTube)

- [ ] Unggah dengan visibilitas **Publik** atau **Tidak publik (unlisted)**. **Jangan Pribadi**, karena juri tidak akan bisa membukanya.
- [ ] Buka link video di jendela penyamaran untuk memastikan.
- [ ] Tulis atribusi (bagian di bawah) di deskripsi video.

Alur yang disarankan (sekitar 9 menit):

| Menit | Isi |
|---|---|
| 0:00–0:45 | Masalah: genset, kamera, dan kunci pintu markas tersambung jaringan, tidak bisa dipasangi antivirus, petugas jaga bukan ahli siber |
| 0:45–1:30 | Solusi dan kalimat inti, gambar cara kerja |
| 1:30–4:00 | Demo skenario 1 di lab: serangan ke genset → isolasi otomatis → kiriman penyerang berikutnya gagal → daftar karantina MikroTik → penjelasan dan centang langkah |
| 4:00–5:30 | Skenario 2 (kamera bocor) dan 3 (sinyal berkala): petugas yang memutuskan |
| 5:30–6:30 | Skenario 4: catatan bukti diubah lalu ketahuan, kode buku jaga |
| 6:30–7:15 | Bukti mandiri: sambungan internet kotak diputus, kotak tetap bekerja |
| 7:15–8:15 | Arsitektur, teknologi, dan pagar pengaman AI |
| 8:15–9:00 | Kelayakan: biaya per kotak, pemasangan bertahap, rencana lanjutan. Penutup dengan kalimat inti |

Naskah lengkap setiap skenario ada di [belajar/11-demo-dan-tanya-jawab.md](belajar/11-demo-dan-tanya-jawab.md).

### 5. Slide penjelasan

Kerangka yang disarankan (12–15 slide):

1. Judul: Pos Jaga Siber, nama tim, kategori Penangkalan
2. Masalah di markas (IT dan OT)
3. Solusi dalam satu kalimat
4. Cara kerja (gambar: Suricata → pjs → MikroTik, AI, catatan bukti, dashboard)
5. Fitur utama
6. Arsitektur dan alur satu serangan ([belajar/09](belajar/09-tur-kode.md))
7. Teknologi yang dipakai
8. Tampilan dashboard (screenshot)
9. Pagar pengaman: AI hanya menjelaskan, blokir dengan batas waktu, alamat yang tidak boleh diisolasi
10. Catatan bukti anti-ubah (rantai hash, tanda tangan, kode buku jaga)
11. Hasil uji di lab (angka nyata)
12. Kelayakan: biaya, cara pemasangan di satuan, rencana lanjutan
13. Batas purwarupa (jujur)
14. Atribusi
15. Tim

Simpan juga sebagai PDF supaya tampilannya tidak berubah di komputer juri.

## Atribusi

Rulebook membolehkan karya dan alat pihak ketiga **asalkan disebutkan dengan jelas**. Teks ini dipakai di slide dan deskripsi video, dan juga ada di README:

> Komponen pihak ketiga: Suricata (OISF), aturan ET Open (Emerging Threats), MikroTik RouterOS/CHR, Ollama, model Qwen2.5 (tim Qwen, Alibaba Cloud), Python beserta pustaka bawaannya, pustaka cryptography (opsional), algoritma Ed25519 sesuai RFC 8032, dan VirtualBox. Kode dan dokumentasi dikembangkan dengan bantuan asisten AI (Claude, buatan Anthropic).

## Daftar periksa terakhir sebelum menekan kirim

- [ ] Jumlah dan nama anggota tim sudah benar di platform, semua anggota punya akun CODEPOLITAN
- [ ] Repositori publik dan bisa dibuka di jendela penyamaran
- [ ] Demo berjalan dari unduhan baru
- [ ] Thumbnail 1200 × 630, maksimal 500 KB
- [ ] Paling banyak 5 screenshot
- [ ] Video maksimal 10 menit, bisa dibuka tanpa masuk akun
- [ ] Slide (PDF) sudah diunggah
- [ ] Atribusi ada di README, slide, dan deskripsi video
- [ ] Simpan tangkapan layar halaman konfirmasi pengumpulan

## Kalau lolos ke final

- **Minimal 1 orang wajib hadir** di Hotel Aston Kartika, Jakarta, Selasa 24 November. Tim finalis yang tidak hadir otomatis gugur.
- Presentasi **10 menit per tim, sudah termasuk penjelasan, demo, dan tanya jawab.** Naskahnya ada di [belajar/11](belajar/11-demo-dan-tanya-jawab.md).
- Bawa laptop dengan lab virtual yang sudah teruji, lampu genset kalau ada, dan rekaman video cadangan.
- Subsidi transportasi Rp500.000 per tim diberikan saat hadir di lokasi.
