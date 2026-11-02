# 02 · IT, OT, dan Modbus

## 1. Dua dunia di satu markas

| | IT (teknologi informasi) | OT (teknologi operasional) |
|---|---|---|
| Contoh | Laptop staf, server berkas, printer | Genset, kamera CCTV, kunci pintu elektronik, pompa air, panel listrik |
| Yang dijaga | **Data**: rahasia, tidak bocor | **Benda fisik**: tetap menyala, tetap aman |
| Kalau diserang | Data dicuri atau dikunci | Listrik padam, pintu terbuka, kamera buta |
| Umur perangkat | 3–5 tahun, sering diperbarui | 10–20 tahun, jarang disentuh |
| Bisa dipasang antivirus? | Bisa | Biasanya **tidak bisa** |

Inilah alasan utama kotak ini dibuat: **peralatan OT tidak bisa menjaga dirinya sendiri.** Genset tidak bisa dipasangi antivirus. Satu-satunya cara menjaganya adalah mengawasi **lalu lintas jaringan** yang menuju ke sana.

## 2. Kenapa OT rentan

- **Dibuat untuk jaringan tertutup.** Bahasa yang dipakai peralatan dirancang puluhan tahun lalu, saat belum terpikir ada penyerang di jaringan.
- **Tanpa kata sandi.** Siapa pun yang bisa "berbicara" ke genset bisa memberinya perintah.
- **Jarang diperbarui.** Celah keamanan bisa bertahan bertahun-tahun.
- **Kata sandi bawaan pabrik.** Banyak kamera dan perekam CCTV masih memakai `admin/admin` atau `admin/12345`.

## 3. Serangan OT yang pernah terjadi

| Kejadian | Ringkasan | Pelajaran untuk markas |
|---|---|---|
| Stuxnet (ditemukan 2010) | Program jahat merusak mesin sentrifugal pengayaan uranium di Iran. Masuk lewat flashdisk ke jaringan yang tidak tersambung internet | Jaringan tanpa internet tetap bisa diserang dari dalam |
| Jaringan listrik Ukraina (Desember 2015) | Penyerang mengendalikan sistem distribusi dari jarak jauh. Ratusan ribu pelanggan padam selama beberapa jam | Perintah ke peralatan listrik bisa dikirim penyerang |
| Mirai (2016) | Ratusan ribu kamera CCTV, perekam video, dan router dengan sandi bawaan diambil alih lewat Telnet, lalu dipakai menyerang situs besar | Kamera murah adalah pintu masuk yang umum |
| Triton (2017) | Program jahat menyasar sistem keselamatan di fasilitas petrokimia | Penyerang mengincar sistem yang justru dibuat untuk mencegah kecelakaan |
| Colonial Pipeline (2021) | Serangan ransomware di sisi IT membuat perusahaan menghentikan pipa bahan bakar selama beberapa hari | Serangan di IT bisa berdampak ke OT |

Aturan kotak (bab 04) dan skenario demo diambil dari pola-pola ini: perintah asing ke peralatan, kamera yang bocor keluar, perangkat asing, dan program jahat yang "melapor" ke pengendalinya.

## 4. Modbus: bahasa genset

**Modbus** dibuat tahun 1979 dan sampai sekarang menjadi salah satu bahasa yang paling banyak dipakai peralatan industri. Versi jaringannya, **Modbus TCP**, memakai port **502**.

Hal terpenting tentang Modbus: **tidak ada kata sandi dan tidak ada enkripsi.** Kalau sebuah laptop bisa menjangkau port 502 genset, laptop itu bisa menyuruh genset mati.

### Isi "kepala" peralatan

Modbus memandang peralatan sebagai kumpulan kotak kecil bernomor:

| Jenis | Ukuran | Bisa ditulis? | Contoh di genset tiruan |
|---|---|---|---|
| Coil | 1 bit (nyala/mati) | Ya | Coil 0 = genset menyala (1) atau mati (0) |
| Discrete input | 1 bit | Tidak | (tidak dipakai) |
| Input register | 16 bit (angka 0–65535) | Tidak | (tidak dipakai) |
| Holding register | 16 bit | Ya | Register 0 = volt, 1 = Hz, 2 = bahan bakar % |

### Kode fungsi

Setiap perintah Modbus diawali **kode fungsi**:

| Kode | Arti | Baca/tulis |
|---|---|---|
| 1 | Baca coil | Baca |
| 2 | Baca discrete input | Baca |
| 3 | Baca holding register | Baca |
| 4 | Baca input register | Baca |
| 5 | Tulis satu coil | **Tulis** |
| 6 | Tulis satu register | **Tulis** |
| 15 | Tulis banyak coil | **Tulis** |
| 16 | Tulis banyak register | **Tulis** |

Aturan Suricata nomor 1 di proyek ini menangkap semua perintah **tulis** dari perangkat yang bukan pengendali resmi.

### Membedah satu perintah "matikan genset"

Skrip `lab/serangan_genset.py` mengirim 12 byte ini (ditulis dalam heksadesimal):

```
00 01   00 00   00 06   01   05   00 00   00 00
└─┬─┘   └─┬─┘   └─┬─┘   ┬    ┬    └─┬─┘   └─┬─┘
  │       │       │     │    │      │       └─ nilai: 0x0000 = MATI (0xFF00 = NYALA)
  │       │       │     │    │      └───────── alamat coil: 0
  │       │       │     │    └──────────────── kode fungsi 5: tulis satu coil
  │       │       │     └───────────────────── nomor unit (perangkat) 1
  │       │       └─────────────────────────── panjang sisa pesan: 6 byte
  │       └─────────────────────────────────── nomor protokol: selalu 0
  └─────────────────────────────────────────── nomor transaksi (bebas, untuk mencocokkan balasan)
```

Tujuh byte pertama disebut **kepala MBAP**. Sisanya disebut **PDU**: kode fungsi dan datanya. Di Python, kepala ini dibuat dengan satu baris:

```python
struct.pack(">HHHBBHH", 1, 0, 6, 1, 5, 0, 0x0000)
```

`>` artinya urutan byte "besar di depan" (big-endian), `H` = 2 byte, `B` = 1 byte.

### Membaca balasan

Saat proyek ini diuji, genset tiruan membalas permintaan "baca register 0–2" dengan:

```
00 02 00 00 00 09 01 03 06 00 dc 00 32 00 57
                     │  │  └─┬─┘ └─┬─┘ └─┬─┘
                     │  │    │     │     └─ 0x57 = 87  (bahan bakar 87%)
                     │  │    │     └─────── 0x32 = 50  (50 Hz)
                     │  │    └───────────── 0xdc = 220 (220 volt)
                     │  └────────────────── 6 byte data menyusul
                     └───────────────────── kode fungsi 3
```

## 5. Genset tiruan di proyek ini

`lab/genset_tiruan.py` adalah server Modbus kecil yang berpura-pura menjadi genset:

- melayani kode fungsi 1, 3, 5, dan 15,
- menampilkan lampu di `http://localhost:8081`,
- mencatat siapa yang memberi perintah,
- bisa menggerakkan lampu sungguhan lewat ESP32 (`--serial`).

## Latihan

1. Jalankan genset tiruan:

   ```bash
   python lab/genset_tiruan.py
   ```

   Buka http://localhost:8081.

2. Di terminal lain, baca keadaan genset:

   ```python
   import socket, struct
   s = socket.create_connection(("127.0.0.1", 5020))
   s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 3, 0, 3))   # baca 3 register mulai dari 0
   print(s.recv(256).hex(" "))
   ```

   Cocokkan hasilnya dengan tabel di atas.

3. Matikan genset dengan skrip serangan, lalu lihat lampunya:

   ```bash
   python lab/serangan_genset.py --target 127.0.0.1 --port 5020
   ```

4. Tulis sendiri perintah untuk **menyalakan** genset (petunjuk: nilai coil 0xFF00).

## Kamu paham kalau...

- bisa menjelaskan kenapa genset tidak bisa menjaga dirinya sendiri,
- tahu bahwa Modbus tidak punya kata sandi, dan apa akibatnya,
- bisa menunjuk byte mana dalam perintah Modbus yang berarti "tulis" dan mana yang berarti "mati".
