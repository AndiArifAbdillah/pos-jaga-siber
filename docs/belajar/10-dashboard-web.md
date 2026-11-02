# 10 · Dashboard web

Dashboard adalah satu-satunya bagian yang dilihat petugas jaga. Karena itu ia dirancang untuk **orang yang bukan ahli**, sedang lelah, dan mungkin sedang panik.

## 1. Tiga bahasa halaman web

| Berkas | Bahasa | Mengatur |
|---|---|---|
| `web/index.html` | HTML | **Isi dan susunan**: kotak ringkasan, daftar kejadian, panel rincian |
| `web/gaya.css` | CSS | **Tampilan**: warna, ukuran huruf, tata letak |
| `web/aplikasi.js` | JavaScript | **Perilaku**: mengambil data, menggambar ulang, tombol |

## 2. Prinsip desain

| Prinsip | Wujudnya di layar |
|---|---|
| Yang pertama dilihat adalah **yang harus diputuskan** | Kotak pertama "Perlu keputusan Anda", bukan "jumlah serangan" |
| Bahasa sehari-hari | Kartu "Apa yang terjadi", "Kenapa berbahaya", "Langkah (SOP)" |
| Peralatan dipisah dari komputer | Daftar "Peralatan (OT)" dan "Komputer (IT)" |
| Bukti selalu terlihat | Kode buku jaga besar, status rantai di kanan atas |
| Tetap berfungsi tanpa internet | **Tidak ada** huruf, gambar, atau pustaka dari internet. Semua berkas dilayani kotak |
| Warna punya arti tetap | Merah = kritis/diisolasi, kuning = tinggi/baru, biru = sedang, hijau = normal |

Huruf memakai `system-ui`, yaitu huruf bawaan sistem operasi, supaya halaman tetap rapi walaupun tanpa internet.

## 3. Cara halaman bekerja

```
setiap 2 detik:  fetch("/api/status") ──► state.data ──► render()
                                                         ├─ renderChips()     chip di kanan atas
                                                         ├─ renderTiles()     4 kotak ringkasan
                                                         ├─ renderList()      daftar kejadian
                                                         ├─ renderDetail()    panel rincian
                                                         ├─ renderDevices()   daftar perangkat
                                                         └─ renderEvidence()  catatan bukti
```

Cara ini disebut **polling**: bertanya berkala. Lebih sederhana daripada sambungan dua arah (WebSocket), dan cukup untuk jaringan lokal.

`renderDetail` hanya menggambar ulang kalau data kejadian yang dipilih **berubah** (dibandingkan dengan `state.detailKey`). Tanpa ini, panel rincian berkedip setiap 2 detik dan mengganggu petugas yang sedang membaca.

### Tombol

Semua tombol memanggil `act(id, aksi)`, yang mengirim:

```js
fetch(`/api/insiden/${id}/${aksi}`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-PJS": "1" },
  body: JSON.stringify({ operator: state.operator }),
});
```

Nama operator diambil dari kolom di kanan atas dan diingat di browser itu saja (`localStorage`). Setiap tindakan tercatat di catatan bukti dengan nama tersebut.

Tombol **Isolasi perangkat** meminta konfirmasi dulu (`window.confirm`), karena isolasi memutus perangkat dari jaringan.

## 4. Dua pengaman penting

### Menangkal teks berbahaya (XSS)

Data di dashboard sebagian berasal dari **jaringan**: nama domain, pesan aturan, nama perangkat. Penyerang bisa sengaja membuat nama domain berisi kode, misalnya `<img src=x onerror=...>`. Kalau teks itu ditempel apa adanya ke halaman, kodenya **ikut berjalan** di browser petugas. Serangan ini disebut **XSS**.

Karena itu, **semua** teks dari data dilewatkan fungsi `esc()` sebelum ditampilkan:

```js
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
```

Aturannya: **setiap kali menambah tampilan baru, bungkus data dengan `esc()`.** Laporan cetak di `server.py` memakai `html.escape` untuk alasan yang sama.

### Menangkal tombol ditekan dari situs lain (CSRF)

Tanpa pengaman, sebuah situs jahat yang dibuka petugas bisa diam-diam mengirim `POST` ke `http://10.10.0.2:8080/api/insiden/.../lepas` dan melepas isolasi. Serangan ini disebut **CSRF**.

Pengamannya: setiap `POST` wajib membawa kepala `X-PJS: 1`. Browser **tidak mengizinkan** situs lain menambahkan kepala khusus ke permintaan lintas situs tanpa persetujuan server. Server kotak tidak pernah memberi persetujuan itu, jadi permintaan dari situs lain ditolak dengan kode 403.

## 5. Tata letak di berbagai layar

`gaya.css` memakai **CSS Grid**:

- layar lebar: tiga kolom (daftar, rincian, samping),
- di bawah 1200 px: dua kolom, panel samping pindah ke bawah,
- di bawah 800 px (ponsel): satu kolom.

Coba perkecil jendela browser saat demo untuk melihatnya.

## 6. Laporan siap cetak

Tombol **Buat laporan** membuka `/laporan/<id>`: halaman sederhana berisi rincian kejadian, penjelasan, centang langkah, jejak di catatan bukti, kode buku jaga, dan kolom tanda tangan. Tekan **Cetak** untuk mencetak atau menyimpan sebagai PDF.

## Latihan

1. Ganti warna aksen (`--accent` di `gaya.css`) dan muat ulang halaman.
2. Tambahkan kotak ringkasan kelima: "Kejadian hari ini". Petunjuk: tambah `<div class="tile">` di `index.html`, lalu hitung di `renderTiles()`.
3. Uji XSS dengan aman: ubah satu nama perangkat di `config.demo.json` menjadi `<b>Genset</b>`, jalankan demo. Apakah tulisannya tebal atau tampil apa adanya? Kenapa?
4. Buka alat pengembang browser (F12) → Network. Amati permintaan `/api/status` setiap 2 detik dan isinya.

## Kamu paham kalau...

- bisa menjelaskan alur data dari `/api/status` sampai layar,
- tahu kenapa semua teks harus melewati `esc()`,
- bisa menambah satu elemen di dashboard tanpa merusak yang lain.
