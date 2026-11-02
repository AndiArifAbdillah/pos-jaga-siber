# 04 · Suricata: "mata" kotak

**Suricata** adalah program pendeteksi serangan jaringan yang gratis dan terbuka (open source), dibuat oleh yayasan OISF. Dipakai luas oleh perusahaan dan pemerintah di banyak negara. Kotak memakai Suricata untuk membaca paket, lalu program kita (`pjs`) membaca hasil catatan Suricata.

Kenapa tidak membuat pembaca paket sendiri? Karena membaca paket dengan benar itu sulit: menyambung potongan TCP, memahami puluhan bahasa (HTTP, DNS, TLS, Modbus, SMB), dan tetap cepat. Suricata sudah mengerjakannya selama lebih dari 10 tahun. Inovasi kita ada di **apa yang dilakukan setelah Suricata melihat sesuatu**.

## 1. Alur kerja Suricata

```
paket ──► 1. tangkap ──► 2. buka lapisan ──► 3. susun percakapan ──► 4. pahami bahasa ──► 5. cocokkan aturan ──► 6. tulis catatan
          (af-packet)    (Ethernet, IP,      (flow dan aliran       (HTTP, DNS, TLS,     (ribuan aturan)       (eve.json)
                          TCP/UDP)            TCP utuh)              Modbus, ...)
```

1. **Tangkap:** mengambil paket dari kartu jaringan. Di Linux memakai cara bernama `af-packet`.
2. **Buka lapisan:** membaca amplop Ethernet, IP, TCP/UDP (lihat bab 01).
3. **Susun percakapan:** mengelompokkan paket menjadi **flow** dan menyusun potongan TCP sesuai urutan.
4. **Pahami bahasa:** mengenali bahasa lapisan aplikasi. Untuk Modbus, Suricata tahu mana kode fungsi, alamat, dan nilai.
5. **Cocokkan aturan:** setiap aturan diperiksa terhadap lalu lintas.
6. **Tulis catatan:** hasilnya ditulis ke `eve.json`, satu baris JSON per kejadian.

## 2. Anatomi satu aturan

Aturan nomor 1 di `aturan/pjs-ot.rules`:

```
alert modbus !$PJS_PENGENDALI_OT any -> $PJS_OT any (msg:"PJS OT perintah tulis Modbus dari perangkat yang bukan pengendali"; flow:to_server,established; modbus: access write; classtype:attempted-admin; metadata:pjs_jenis ot_tulis, pjs_tingkat kritis; sid:1990001; rev:1;)
```

Dibaca seperti kalimat:

| Bagian | Isi | Artinya |
|---|---|---|
| Tindakan | `alert` | Bunyikan peringatan. (Ada juga `pass`, `drop`, `reject`, tetapi `drop` hanya berlaku kalau Suricata dipasang di tengah jalur sebagai IPS) |
| Protokol | `modbus` | Hanya lalu lintas yang dikenali sebagai Modbus |
| Asal | `!$PJS_PENGENDALI_OT any` | Dari alamat mana pun **kecuali** pengendali resmi, port berapa pun |
| Arah | `->` | Dari asal ke tujuan |
| Tujuan | `$PJS_OT any` | Ke peralatan, port berapa pun |
| `msg` | "PJS OT perintah tulis ..." | Pesan yang ditulis di catatan |
| `flow` | `to_server,established` | Paket dari klien ke server, pada sambungan yang sudah terbentuk |
| `modbus` | `access write` | Perintah Modbus jenis **tulis** (kode 5, 6, 15, 16, dan sejenisnya) |
| `classtype` | `attempted-admin` | Golongan serangan: mencoba mengambil alih |
| `metadata` | `pjs_jenis ot_tulis, pjs_tingkat kritis` | Label tambahan yang **dibaca kotak** untuk menentukan jenis dan tingkat kejadian |
| `sid` | `1990001` | Nomor unik aturan |
| `rev` | `1` | Versi aturan. Naikkan setiap kali aturan diubah |

### Variabel alamat

`$PJS_OT`, `$PJS_OT_NET`, dan `$PJS_PENGENDALI_OT` diisi di `suricata.yaml` (lihat `aturan/suricata-tambahan.yaml`). Jadi aturan yang sama bisa dipakai di markas mana pun. Cukup ubah variabelnya.

### Nomor aturan (sid)

Rentang `1000000–1999999` disepakati untuk aturan buatan sendiri, supaya tidak bertabrakan dengan aturan publik. Aturan ET Open memakai rentang `2000000` ke atas. Aturan PJS memakai `1990001` dan seterusnya.

### Membatasi banjir peringatan

Aturan 2 dan 3 memakai:

```
threshold:type limit, track by_src, count 1, seconds 300;
```

Artinya: dari satu alamat asal, paling banyak **satu** peringatan setiap **300 detik**. Tanpa ini, pemindai yang mencoba ribuan kali akan membanjiri layar.

## 3. Aturan umum: ET Open

Selain 3 aturan PJS, Suricata memakai ribuan aturan publik gratis bernama **ET Open** (Emerging Threats). Diunduh dan diperbarui dengan:

```bash
sudo suricata-update
```

Peringatan dari aturan ini tidak punya `metadata pjs_jenis`. Kotak menentukan tingkatnya dari nilai `severity` Suricata (1 = tinggi, 2 = sedang). Peringatan severity 3 diabaikan supaya layar tidak penuh (`suricata_lowest_severity`).

Memperbarui aturan butuh internet. Di markas tanpa internet, aturan bisa diunduh di tempat lain lalu dibawa dengan flashdisk yang sudah diperiksa, atau dikirim dari pusat saat kotak tersambung.

## 4. Isi eve.json

Satu peringatan genset di `eve.json` (dirapikan supaya mudah dibaca):

```json
{
  "timestamp": "2026-11-12T15:20:01.123456+0700",
  "flow_id": 2002,
  "in_iface": "enp0s9",
  "event_type": "alert",
  "src_ip": "10.10.0.66",  "src_port": 51544,
  "dest_ip": "10.20.0.10", "dest_port": 502,
  "proto": "TCP",
  "app_proto": "modbus",
  "ether": {"src_mac": "08:00:27:aa:00:02", "dest_mac": "24:0a:c4:20:00:10"},
  "alert": {
    "signature_id": 1990001,
    "signature": "PJS OT perintah tulis Modbus dari perangkat yang bukan pengendali",
    "severity": 1,
    "metadata": {"pjs_jenis": ["ot_tulis"], "pjs_tingkat": ["kritis"]}
  },
  "modbus": {"request": {"function_code": "WriteSingleCoil", "write": {"address": 0, "data": 0}}}
}
```

Selain `alert`, Suricata juga menulis jenis catatan lain: `flow` (ringkasan satu percakapan), `dns`, `tls`, `http`, dan lainnya. Kotak memakai `flow`, `tls`, dan `http` untuk aturan dasar (peralatan ke luar dan sinyal berkala), lalu memakai `ether` untuk mengenali MAC perangkat.

Perhatikan `src_mac` di atas adalah MAC **router**, bukan MAC laptop penyerang. Paket itu dilihat di jaringan peralatan setelah melewati router (bab 01 bagian 3). Itulah gunanya `router_macs` di konfigurasi.

Contoh lengkap ada di `lab/contoh_eve.jsonl`. Berkas itu yang diputar oleh `python -m pjs demo --putar`.

## 5. Bagaimana kotak membaca hasil Suricata

`pjs/collector.py` membaca `eve.json` baris demi baris seperti perintah `tail -f`. Setiap baris diserahkan ke `Detector.process` (`pjs/detector.py`). Untuk peringatan, `_on_alert`:

1. mengambil `metadata.pjs_jenis` dan `metadata.pjs_tingkat`,
2. kalau tidak ada, mencocokkan `signature_id` dengan `SID_FALLBACK` di `pjs/playbook.py`,
3. kalau tetap tidak ada, memperlakukannya sebagai aturan umum dengan tingkat dari `severity`.

## 6. Perintah Suricata yang berguna

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml -v     # uji konfigurasi tanpa menjalankan
sudo systemctl status suricata                          # apakah berjalan
sudo tail -f /var/log/suricata/eve.json                 # lihat catatan langsung
sudo tail -f /var/log/suricata/suricata.log             # pesan galat Suricata
sudo suricata-update                                    # perbarui aturan ET Open
sudo suricatasc -c reload-rules                         # muat ulang aturan tanpa mematikan
```

## Latihan

1. **Rekam lalu putar ulang.** Di lab, rekam serangan dengan tcpdump, lalu suruh Suricata membaca rekaman itu:

   ```bash
   sudo tcpdump -i enp0s9 -w serangan.pcap port 502      # hentikan dengan Ctrl+C setelah serangan
   sudo suricata -c /etc/suricata/suricata.yaml -r serangan.pcap -l /tmp/hasil
   grep '"alert"' /tmp/hasil/eve.json
   ```

   Cara ini berguna untuk menguji aturan baru tanpa mengulang serangan.

2. **Tulis aturan baru.** Buat aturan sid `1990004` yang memberi peringatan *tinggi* kalau ada perintah tulis **register** (kode fungsi 6) ke genset dari mana pun. Petunjuk: `modbus: function 6;`. Jangan lupa `metadata:pjs_jenis ot_tulis, pjs_tingkat tinggi;`.

3. Kenapa aturan 1 memakai `!$PJS_PENGENDALI_OT` dan bukan `$EXTERNAL_NET`?

4. Buka `lab/contoh_eve.jsonl`. Temukan satu catatan `flow` dan satu catatan `alert`. Apa bedanya?

## Kamu paham kalau...

- bisa membaca aturan PJS dan menjelaskan setiap bagiannya,
- tahu jenis-jenis catatan di `eve.json` dan mana yang dipakai kotak,
- bisa menguji aturan baru dengan berkas rekaman `.pcap`.
