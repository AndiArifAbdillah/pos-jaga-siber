# 03 · Ancaman dan pertahanan

## 1. Ancaman yang dijaga kotak ini

| Ancaman | Contoh di markas | Cara kotak mengenalinya | Jenis di kode |
|---|---|---|---|
| Perintah asing ke peralatan | Laptop tamu mematikan genset | Aturan Suricata: perintah tulis Modbus dari perangkat yang bukan pengendali | `ot_tulis` |
| Mengintip peralatan | Ada yang membaca keadaan genset dari jaringan kantor | Aturan Suricata: baca Modbus dari luar jaringan peralatan | `ot_baca_luar` |
| Membobol peralatan | Mencoba masuk kamera lewat Telnet | Aturan Suricata: sambungan ke port 23/2323 peralatan | `ot_telnet` |
| Peralatan bocor keluar | Kamera mengunggah rekaman ke server luar | Aturan dasar: perangkat jaringan peralatan menghubungi alamat luar | `ot_ke_luar` |
| Program jahat "melapor" | Laptop terinfeksi menghubungi pengendalinya setiap 20 detik | Aturan dasar: sambungan berulang dengan jarak waktu nyaris sama | `sinyal_berkala` |
| Perangkat asing | Ada perangkat yang belum pernah terlihat | Aturan dasar: alamat baru setelah masa belajar | `perangkat_baru` |
| Perangkat dikuasai, ancaman baru | Kunci pintu tiba-tiba menghubungi banyak perangkat lain untuk mencari sasaran | AI deteksi perilaku (machine learning, bab 13) | `perilaku_aneh` |
| Pola serangan umum | Pemindaian, eksploit yang sudah dikenal | Aturan Suricata umum (ET Open) | `umum:<nomor>` |
| Menghapus jejak | Orang dalam menghapus catatan kejadian | Rantai catatan bukti putus | (catatan bukti) |

Serangan **tidak harus datang dari internet.** Banyak yang berasal dari dalam: flashdisk, laptop tamu, Wi-Fi tamu, atau orang dalam. Karena itu kotak mengawasi lalu lintas **di dalam** markas, bukan hanya pintu keluar ke internet.

## 2. Tiga jenis penjaga

| Penjaga | Cara kerja | Perumpamaan |
|---|---|---|
| **Firewall** | Aturan tetap: alamat/port mana yang boleh lewat | Palang pintu dengan daftar tamu |
| **IDS** (Intrusion Detection System) | Melihat salinan lalu lintas dan membunyikan alarm | CCTV dengan petugas yang mengawasi |
| **IPS** (Intrusion Prevention System) | Berdiri di tengah jalur dan bisa langsung membuang paket | Petugas yang berdiri di pintu dan bisa menahan orang |

Pos Jaga Siber adalah **IDS** (pasif, melihat salinan) **yang bisa meminta firewall bertindak** (lewat MikroTik). Gabungan ini kadang disebut "respons otomatis".

### Kenapa tidak langsung IPS?

IPS berdiri di tengah jalur. Kalau IPS macet atau salah, **jaringan ikut berhenti**: genset bisa tidak bisa dikendalikan sama sekali. Untuk jaringan peralatan, itu terlalu berisiko. Dengan cara pasif:

- kalau kotak mati, jaringan tetap berjalan normal,
- blokir hanya terjadi untuk kejadian **kritis** pada peralatan, dan
- blokir punya **batas waktu** (24 jam) sehingga kesalahan tidak berlangsung selamanya.

## 3. Aturan tanda tangan dan aturan perilaku

Ada dua cara mengenali serangan:

1. **Tanda tangan (signature):** mencari pola yang sudah diketahui, seperti mencocokkan sidik jari. Contohnya aturan Suricata. Kelebihannya tepat. Kekurangannya, serangan baru yang belum punya pola tidak tertangkap.
2. **Perilaku (baseline / anomali):** mempelajari apa yang normal, lalu memperhatikan yang menyimpang. Contohnya "perangkat baru", "sinyal berkala", dan **AI deteksi perilaku** yang memakai machine learning (bab 13). Kelebihannya bisa menangkap hal baru. Kekurangannya bisa salah alarm.

Kotak memakai keduanya.

### Masa belajar

Saat pertama dipasang, kotak belum tahu perangkat mana yang normal. Selama **masa belajar** (bawaan 14 hari, `learning_hours: 336`), setiap perangkat yang terlihat dicatat diam-diam sebagai normal. Setelah masa belajar selesai, perangkat yang baru muncul akan dilaporkan.

### Mengatasi alarm palsu

Setiap penjaga bisa salah alarm. Kotak menyediakan tombol **Bukan ancaman**: kejadian serupa (jenis, asal, dan tujuan yang sama) tidak akan dibunyikan lagi. Tombol ini dicatat di catatan bukti, jadi bisa diperiksa siapa yang menekannya.

## 4. Memutuskan: otomatis atau petugas?

```
              kejadian baru
                    │
        ┌───────────┴───────────┐
        │ kritis DAN menyangkut  │
        │ jaringan peralatan?    │
        └───────────┬───────────┘
            ya      │      tidak
        ┌───────────┴───────────┐
        ▼                       ▼
 isolasi otomatis         jelaskan dulu,
 lalu jelaskan            petugas memutuskan
```

Kenapa hanya kritis + peralatan yang otomatis? Karena untuk genset, **menunggu petugas bisa terlambat**: perintah mati butuh kurang dari satu detik. Untuk kejadian lain, salah blokir lebih merugikan daripada menunggu beberapa menit.

Ada pengaman tambahan: alamat di `never_isolate` (router, kotak itu sendiri) **tidak pernah** diisolasi, supaya kotak tidak memutus jaringan markas karena kesalahan.

## 5. Prinsip yang dipegang proyek ini

- **AI tidak pernah memutuskan blokir.** Blokir hanya dari aturan tetap yang bisa diperiksa. AI hanya menjelaskan.
- **Hanya metadata.** Kotak tidak menyimpan isi percakapan atau berkas, hanya "siapa ke siapa, kapan, berapa banyak".
- **Semua tindakan tercatat.** Termasuk tindakan petugas.
- **Mandiri.** Semua fungsi berjalan di dalam kotak, tanpa layanan luar.

## Latihan

1. Jalankan demo. Untuk setiap kejadian yang muncul, tunjuk baris tabel di bagian 1 yang cocok.
2. Kenapa kejadian "Kamera mengirim data ke luar" tidak diisolasi otomatis, padahal tingkatnya tinggi?
3. Buka `config.demo.json`. Apa yang terjadi kalau alamat `10.10.0.1` dihapus dari `never_isolate`, lalu router mengirim perintah tulis ke genset?
4. Sebutkan satu contoh alarm palsu "sinyal berkala" yang mungkin terjadi di markas (petunjuk: program yang memeriksa pembaruan secara teratur).

## Kamu paham kalau...

- bisa menjelaskan beda firewall, IDS, dan IPS dengan perumpamaan,
- bisa menjelaskan kenapa kotak pasif lebih aman untuk jaringan peralatan,
- bisa menjelaskan kapan kotak bertindak sendiri dan kapan menunggu petugas.
