# 05 · MikroTik dan blokir: "tangan" kotak

Kotak sendiri tidak bisa menghalangi paket, karena ia hanya menerima **salinan** lalu lintas. Yang bisa menghalangi adalah **router**, karena semua lalu lintas antarjaringan melewatinya. Jadi kotak "meminta tolong" router lewat API.

## 1. MikroTik dan RouterOS

**MikroTik** adalah pembuat router dari Latvia yang sangat banyak dipakai di Indonesia: di kantor, sekolah, warnet, sampai instansi. Sistem operasinya bernama **RouterOS**. **CHR** (Cloud Hosted Router) adalah RouterOS yang berjalan di komputer virtual. Itu yang dipakai di lab.

Cara mengatur RouterOS: **Winbox** (aplikasi Windows), **WebFig** (lewat browser), **Terminal/SSH** (mengetik perintah), dan **API** (dipakai program). Kotak memakai API.

## 2. Firewall RouterOS

### Tiga "rantai" (chain)

| Rantai | Paket apa | Contoh |
|---|---|---|
| `input` | Paket **ke** router itu sendiri | Seseorang membuka Winbox ke router |
| `forward` | Paket yang **melewati** router dari satu jaringan ke jaringan lain | Laptop kantor → genset |
| `output` | Paket **dari** router | Router mengirim catatan ke server |

Serangan laptop ke genset melewati router, jadi aturan blokir dipasang di rantai **forward**.

### Dibaca dari atas ke bawah

Aturan firewall diperiksa **berurutan dari nomor 0**. Aturan pertama yang cocok dan punya tindakan akhir (`accept` atau `drop`) langsung menentukan nasib paket. Karena itu aturan karantina harus berada **paling atas**. Kalau di atasnya ada aturan "terima semua sambungan yang sudah terbentuk", serangan yang sedang berjalan tetap lolos.

**Fasttrack** adalah fitur MikroTik yang mempercepat sambungan dengan melewati sebagian besar firewall. Aturan karantina harus berada di atas aturan fasttrack.

### Daftar alamat (address-list) dengan batas waktu

Daripada membuat aturan baru untuk setiap pelaku, dibuat **satu daftar** bernama `pjs-karantina` dan **dua aturan tetap**:

```
/ip firewall filter add chain=forward src-address-list=pjs-karantina action=drop
/ip firewall filter add chain=forward dst-address-list=pjs-karantina action=drop
```

Artinya: paket **dari** atau **ke** alamat yang ada di daftar itu dibuang. Untuk mengisolasi perangkat, kotak cukup menambahkan alamatnya ke daftar:

```
/ip firewall address-list add list=pjs-karantina address=10.10.0.66 timeout=24h comment="PJS-0002 otomatis"
```

`timeout=24h` artinya router **menghapus sendiri** alamat itu setelah 24 jam. Kalau kotak salah blokir dan tidak ada yang sempat membatalkan, kesalahannya tidak berlangsung selamanya.

Isolasi ini memutus perangkat dari **jaringan lain**. Perangkat di jaringan yang sama tetap bisa saling berbicara, karena paketnya tidak melewati router. Contohnya, kamera yang diisolasi tetap bisa merekam ke perekam CCTV di jaringan peralatan, tetapi tidak bisa mengirim keluar markas.

## 3. Pengaman akun kotak

Skrip `aturan/mikrotik-pjs.rsc` membuat:

- kelompok pengguna `pjs-api` yang hanya boleh `api`, `read`, dan `write` (tidak boleh Winbox, SSH, atau menyalakan ulang router),
- pengguna `pjs` yang hanya boleh masuk dari alamat kotak (`address=10.10.0.2/32`),
- layanan API yang hanya menerima sambungan dari kotak.

Jadi, kalaupun sandi kotak bocor, orang lain tidak bisa memakainya dari komputer lain.

## 4. Protokol API RouterOS

API RouterOS memakai port **8728** (atau 8729 dengan enkripsi TLS). Bahasanya sederhana:

- Satu pesan disebut **kalimat**. Isinya beberapa **kata**, diakhiri kata kosong.
- Setiap kata diawali **panjangnya**, lalu isinya.

Contoh kalimat untuk menambah alamat ke karantina:

```
/ip/firewall/address-list/add
=list=pjs-karantina
=address=10.10.0.66
=timeout=24h
=comment=PJS-0002 otomatis
(kata kosong)
```

Router membalas dengan kalimat yang diawali:

| Awalan | Arti |
|---|---|
| `!re` | Satu baris data (misalnya hasil `print`) |
| `!done` | Perintah selesai |
| `!trap` | Ada galat, pesannya di `=message=` |
| `!fatal` | Sambungan akan ditutup |

### Panjang kata

Panjang ditulis 1 sampai 5 byte, tergantung besarnya:

| Panjang | Cara menulis | Contoh |
|---|---|---|
| kurang dari 128 | 1 byte apa adanya | 26 → `1a` |
| kurang dari 16.384 | 2 byte, ditambah `0x8000` | 300 → `81 2c` |
| kurang dari 2.097.152 | 3 byte, ditambah `0xC00000` | |
| kurang dari 268.435.456 | 4 byte, ditambah `0xE0000000` | |
| lebih besar | `f0` lalu 4 byte | |

Ini persis yang dikerjakan fungsi `encode_length` di `pjs/responder.py`. Tes `tests/test_responder.py` memeriksa setiap batasnya.

### Masuk (login)

RouterOS 6.43 ke atas menerima nama dan sandi langsung:

```
/login
=name=pjs
=password=...
```

RouterOS lama membalas dengan "tantangan" (`=ret=`) dan meminta jawaban MD5. Kode `RouterOSClient.login` menangani keduanya. Karena sandi dikirim tanpa enkripsi di port 8728, layanan API **hanya boleh menerima sambungan dari kotak**. Untuk pemasangan sungguhan, pakai port 8729 (TLS).

## 5. Tur kode `pjs/responder.py`

| Bagian | Tugas |
|---|---|
| `encode_length`, `encode_word`, `encode_sentence` | Mengubah kata menjadi byte sesuai aturan di atas |
| `RouterOSClient._read_length`, `_read_sentence` | Kebalikannya: membaca byte balasan menjadi kata |
| `RouterOSClient.talk` | Kirim satu perintah, kumpulkan semua balasan sampai `!done`, ubah `!trap` menjadi galat |
| `MikroTikResponder.isolate` | Masuk, tambah alamat ke daftar. Kalau sudah ada ("already have such entry"), dianggap berhasil |
| `MikroTikResponder.release` | Cari `.id` entri dengan `print` dan `?address=`, lalu `remove` |
| Mode uji | Kalau `mikrotik.enabled` bernilai `false`, perintah tidak dikirim, hanya dicatat. Dipakai saat demo tanpa MikroTik |

Detektor (`pjs/detector.py`) menambahkan dua pengaman sebelum memanggil responder:

- alamat di `never_isolate` ditolak,
- kalau satu alamat diisolasi karena dua kejadian, membatalkan satu kejadian **tidak** melepas alamatnya selama kejadian lain masih aktif.

## Latihan

1. Di CHR lab, tambahkan alamat ke karantina secara manual, lalu coba ping dari VM klien. Hapus lagi dan ping lagi.

   ```
   /ip firewall address-list add list=pjs-karantina address=10.10.0.66 timeout=2m
   /ip firewall address-list print
   ```

2. Jalankan `python -m pjs --config config.json uji-mikrotik`. Apa nama router yang muncul?
3. Hitung byte panjang untuk kata sepanjang 200 karakter. Cocokkan dengan `encode_length(200)` di Python.
4. Kenapa aturan karantina memeriksa `src-address-list` **dan** `dst-address-list`?

## Kamu paham kalau...

- bisa menjelaskan kenapa kotak butuh router untuk memblokir,
- tahu kenapa aturan karantina harus paling atas dan apa gunanya batas waktu,
- bisa membaca `responder.py` dan menjelaskan isi satu kalimat API.
