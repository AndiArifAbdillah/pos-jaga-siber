# 12 · Kamus istilah

| Istilah | Arti singkat | Bab |
|---|---|---|
| Address-list | Daftar alamat di MikroTik yang dipakai aturan firewall. PJS memakai `pjs-karantina` | 05 |
| af-packet | Cara Suricata mengambil paket dari kartu jaringan di Linux | 04 |
| Alamat IP | Alamat perangkat di jaringan, misalnya `10.20.0.10` | 01 |
| Alamat MAC | Nomor kartu jaringan dari pabrik, misalnya `24:0a:c4:20:00:10` | 01 |
| API | Pintu bagi program untuk memberi perintah ke program lain | 05 |
| ARP | Cara mencari MAC dari alamat IP di jaringan yang sama | 01 |
| Baseline | Gambaran "normal" yang dipelajari kotak selama masa belajar | 03 |
| Big-endian | Urutan byte "besar di depan", dipakai Modbus dan banyak protokol jaringan | 02 |
| Broadcast (siaran) | Alamat untuk semua perangkat di satu jaringan, misalnya `10.20.0.255` | 01 |
| Catatan bukti | Catatan kejadian yang bersambung seperti rantai dan ditandatangani | 07 |
| CHR | Cloud Hosted Router: RouterOS untuk komputer virtual | 05 |
| Coil | Kotak 1 bit di peralatan Modbus, misalnya nyala/mati genset | 02 |
| CSRF | Serangan yang memakai browser korban untuk menekan tombol di situs lain | 10 |
| DHCP | Layanan pembagi alamat IP otomatis | 01 |
| DNS | Layanan pengubah nama menjadi alamat IP | 01 |
| Ed25519 | Algoritma tanda tangan digital yang dipakai catatan bukti | 07 |
| ET Open | Kumpulan ribuan aturan Suricata gratis dari Emerging Threats | 04 |
| eve.json | Berkas catatan Suricata, satu kejadian JSON per baris | 04 |
| Fasttrack | Fitur MikroTik yang mempercepat sambungan dengan melewati firewall | 05 |
| Firewall | Penyaring paket berdasarkan aturan | 03, 05 |
| Flow | Satu percakapan utuh antara dua perangkat | 01, 04 |
| Hash (sidik jari) | Ringkasan pendek berukuran tetap dari sebuah data. PJS memakai SHA-256 | 07 |
| Halusinasi | AI menulis hal yang terdengar benar tetapi karangan | 06 |
| Holding register | Kotak 16 bit di peralatan Modbus yang bisa dibaca dan ditulis | 02 |
| IDS | Sistem pendeteksi serangan yang melihat salinan lalu lintas | 03 |
| IPS | Sistem pencegah serangan yang berdiri di tengah jalur | 03 |
| Isolasi | Memutus perangkat dari jaringan lain lewat router | 05 |
| Isolation Forest | Algoritma machine learning yang menemukan data aneh dengan membelah data secara acak: yang aneh cepat terpisah | 13 |
| IT | Teknologi informasi: komputer, server, data | 02 |
| JSON | Format teks untuk data, misalnya `{"ip": "10.10.0.66"}` | 08 |
| Kode buku jaga | 8 huruf awal sidik jari entri terakhir, disalin ke buku jaga kertas | 07 |
| Kuantisasi | Memperkecil model AI dengan menyimpan angka lebih ringkas | 06 |
| Kunci publik / rahasia | Pasangan kunci tanda tangan: rahasia untuk menandatangani, publik untuk memeriksa | 07 |
| LLM | Model bahasa besar, AI yang menulis teks | 06 |
| Machine learning | Cara membuat program belajar dari contoh data, bukan dari aturan yang ditulis tangan | 13 |
| Masa belajar | Periode awal saat kotak mencatat perangkat normal tanpa membunyikan alarm | 03 |
| Metadata | Data tentang percakapan (siapa, kapan, berapa banyak), bukan isinya | 03 |
| Modbus | Bahasa peralatan industri, tanpa kata sandi, port 502 | 02 |
| NAT | Router mengganti alamat privat dengan alamatnya sendiri saat keluar | 01 |
| Ollama | Program untuk menjalankan model AI di komputer sendiri | 06 |
| OT | Teknologi operasional: peralatan fisik seperti genset dan kamera | 02 |
| OUI | 3 byte pertama MAC yang menunjukkan pabrik | 01 |
| Paket | Satu potongan data yang dikirim lewat jaringan | 01 |
| PDU | Bagian inti pesan Modbus: kode fungsi dan data | 02 |
| Playbook | Daftar jenis kejadian beserta penjelasan bawaan dan langkah SOP (`pjs/playbook.py`) | 09 |
| Polling | Bertanya berkala ke server, cara dashboard memperbarui data | 10 |
| Port | Nomor layanan di satu perangkat, 0–65535 | 01 |
| Port mirror (SPAN) | Fitur switch/router untuk menyalin lalu lintas ke satu colokan | 01 |
| Promiscuous mode | Kartu jaringan menerima semua paket, bukan hanya miliknya | 01 |
| Prompt | Perintah teks yang diberikan ke AI | 06 |
| RAG | Cari data dulu, lalu AI menjawab hanya dari data itu. Dipakai asisten piket | 13 |
| Rantai (chain) firewall | Kelompok aturan MikroTik: `input`, `forward`, `output` | 05 |
| Rentang waktu (window) | Potongan waktu (5 menit, di demo 10 detik) tempat kegiatan perangkat diringkas | 13 |
| Router | Penghubung antarjaringan yang menentukan rute dan memasang firewall | 01 |
| RouterOS | Sistem operasi router MikroTik | 05 |
| SHA-256 | Fungsi hash dengan hasil 256 bit (64 huruf heksadesimal) | 07 |
| sid | Nomor unik aturan Suricata | 04 |
| Skor keanehan | Angka 0–1 dari AI deteksi perilaku. Makin dekat ke 1, makin tidak biasa | 13 |
| Sinyal berkala (beacon) | Sambungan berulang dengan jarak waktu nyaris sama, ciri program jahat | 03 |
| Socket | "Colokan" program ke jaringan | 08 |
| SOP | Prosedur tetap satuan, sumber langkah tindakan | 06 |
| SQLite | Database dalam satu berkas | 08 |
| Suricata | Program pendeteksi serangan jaringan, "mata" kotak | 04 |
| Switch | Penghubung perangkat di satu jaringan | 01 |
| TCP / UDP | Cara pengiriman data: bersambung dan pasti (TCP) atau langsung tanpa cek (UDP) | 01 |
| Telnet | Cara masuk jarak jauh tanpa enkripsi, port 23, berbahaya | 03 |
| Thread | Jalur kerja yang berjalan bersamaan di satu program | 08 |
| Timeout (batas waktu) | Lama alamat berada di karantina sebelum dihapus otomatis | 05 |
| TPM | Chip keamanan untuk menyimpan kunci rahasia agar tidak bisa disalin | 07 |
| XSS | Serangan dengan menyisipkan kode ke halaman web lewat data | 10 |
| Zero-day | Serangan atau celah baru yang belum punya aturan atau tambalan | 13 |
