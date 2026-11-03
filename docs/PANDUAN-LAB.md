# Panduan lab virtual (untuk orang A)

Tujuan: membangun "markas tiruan" lengkap di **satu laptop** memakai VirtualBox, tanpa membeli alat. Hasil akhirnya, keempat skenario demo berjalan dengan Suricata dan MikroTik sungguhan.

Kalau ada istilah yang belum paham, baca dulu [docs/belajar/01-jaringan-dasar.md](belajar/01-jaringan-dasar.md) dan [05-mikrotik-dan-blokir.md](belajar/05-mikrotik-dan-blokir.md).

## 0. Yang dibutuhkan

| Kebutuhan | Keterangan |
|---|---|
| Laptop | RAM minimal 8 GB (16 GB lebih nyaman), ruang kosong 40 GB, fitur virtualisasi (VT-x/AMD-V) aktif di BIOS |
| VirtualBox 7 | Gratis, dari virtualbox.org |
| Ubuntu Server 24.04 LTS | Berkas ISO, gratis, dari ubuntu.com |
| MikroTik CHR | Router virtual resmi MikroTik. Unduh "Cloud Hosted Router", pilih **VDI image**, dari mikrotik.com/download |
| Internet | Hanya saat memasang program. Setelah itu lab berjalan tanpa internet |

Lisensi gratis CHR membatasi kecepatan sekitar 1 Mbps per kartu jaringan. Itu cukup untuk demo.

## 1. Peta lab

```
                         ┌──────────────── MikroTik CHR ───────────────┐
  jaringan "kantor"      │ ether1 10.10.0.1    ether2 10.20.0.1        │   jaringan "peralatan"
  10.10.0.0/24  ─────────┤                                             ├──────── 10.20.0.0/24
     │                   │             ether3 203.0.113.1              │            │
     │                   └──────────────────┬──────────────────────────┘            │
     │                                      │ jaringan "internet-palsu"             │
     │                                      │ 203.0.113.0/24                        │
     ├─ Kotak Pos Jaga  10.10.0.2           └─ VM internet-palsu                    ├─ VM genset 10.20.0.10
     │   (juga mendengar jaringan peralatan)      203.0.113.50 dan .77              │   (+ 10.20.0.21 sebagai kamera)
     └─ VM klien 10.10.0.66                                                         │
         (+ 10.10.0.23 sebagai laptop staf)                                         └─ (Kotak mendengar di sini juga)
```

| VM | RAM | Kartu jaringan | Alamat |
|---|---|---|---|
| MikroTik CHR | 256 MB | 1: kantor, 2: peralatan, 3: internet-palsu | 10.10.0.1, 10.20.0.1, 203.0.113.1 |
| Kotak Pos Jaga (Ubuntu) | 3–6 GB | 1: NAT, 2: kantor, 3: peralatan | 10.10.0.2 (kartu 3 tanpa alamat) |
| Genset (Ubuntu) | 512 MB | 1: peralatan, 2: host-only | 10.20.0.10 dan 10.20.0.21 |
| Klien (Ubuntu) | 512 MB | 1: kantor | 10.10.0.66 dan 10.10.0.23 |
| Internet palsu (Ubuntu) | 512 MB | 1: internet-palsu | 203.0.113.50 dan 203.0.113.77 |

Alamat 203.0.113.x adalah rentang khusus dokumentasi. Di lab ini ia berperan sebagai "internet".

Supaya hemat, satu VM memerankan dua perangkat. Contohnya, VM genset juga memerankan kamera (alamat kedua 10.20.0.21). Skrip lab punya pilihan `--dari` untuk memilih alamat asal.

## 2. Membuat jaringan di VirtualBox

Jaringan "Internal Network" di VirtualBox dibuat cukup dengan **mengetik namanya** di pengaturan kartu jaringan VM. Pakai tiga nama yang sama persis: `kantor`, `peralatan`, `internet-palsu`.

Untuk VM **Kotak Pos Jaga**, buka Settings → Network. Pada kartu 2 dan 3, buka Advanced, lalu setel **Promiscuous Mode: Allow All**. Tanpa ini, kotak hanya melihat lalu lintas miliknya sendiri. Pengaturan ini menggantikan fitur "port mirror" pada switch sungguhan.

## 3. MikroTik CHR

1. Buat VM baru: Type **Other**, Version **Other/Unknown (64-bit)**, RAM 256 MB. Pilih "Use an existing virtual hard disk" lalu pilih berkas `.vdi` CHR.
2. Tiga kartu jaringan: kantor, peralatan, internet-palsu (urutan ini menjadi ether1, ether2, ether3).
3. Nyalakan. Masuk dengan pengguna `admin` tanpa sandi, lalu buat sandi baru saat diminta.
4. Ketik:

```
/system identity set name=router-markas
/ip address add address=10.10.0.1/24 interface=ether1
/ip address add address=10.20.0.1/24 interface=ether2
/ip address add address=203.0.113.1/24 interface=ether3
```

5. Tempel isi [aturan/mikrotik-pjs.rsc](../aturan/mikrotik-pjs.rsc) baris demi baris. Ganti sandinya dulu. Firewall CHR baru masih kosong, jadi hapus `place-before=0` pada baris aturan pertama.
6. Periksa: `/ip firewall filter print` harus menampilkan dua aturan "PJS: karantina".

## 4. Kotak Pos Jaga (Ubuntu Server)

### 4a. Pasang Ubuntu dan atur jaringan

Pasang Ubuntu Server seperti biasa. Kartu 1 (NAT) dipakai untuk internet saat memasang program. Setelah itu, buat berkas `/etc/netplan/60-pjs.yaml`:

```yaml
network:
  version: 2
  ethernets:
    enp0s8:
      addresses: [10.10.0.2/24]
    enp0s9:
      dhcp4: false
      dhcp6: false
```

Lalu jalankan `sudo netplan apply`. Cek dengan `ip -br addr`. Nama `enp0s8` dan `enp0s9` biasanya milik kartu 2 dan 3 di VirtualBox, tapi pastikan dengan `ip -br link`.

### 4b. Pasang Suricata

```bash
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt update
sudo apt install -y suricata git python3
sudo suricata-update            # mengunduh aturan umum ET Open
```

Ambil kode proyek (repositori privat: anggota tim harus diundang dulu di GitHub):

```bash
git clone https://github.com/AndiArifAbdillah/pos-jaga-siber.git
cd pos-jaga-siber
sudo cp aturan/pjs-ot.rules /etc/suricata/rules/
```

Ubah `/etc/suricata/suricata.yaml` sesuai [aturan/suricata-tambahan.yaml](../aturan/suricata-tambahan.yaml): alamat jaringan, Modbus dinyalakan, dua kartu af-packet, `ethernet: yes` di eve-log, dan berkas aturan PJS. Lalu:

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml -v   # harus berakhir dengan "Configuration provided was successfully loaded"
sudo systemctl restart suricata
sudo tail -f /var/log/suricata/eve.json              # harus mulai muncul baris-baris JSON
```

### 4c. Pasang AI lokal (Ollama)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b
```

Kalau RAM VM 6 GB atau lebih, boleh mencoba model yang lebih besar (lihat [06-ai-lokal.md](belajar/06-ai-lokal.md)).

### 4d. Jalankan kotak

```bash
cp config.contoh.json config.json
nano config.json        # isi sandi MikroTik dan daftar perangkat lab
sudo mkdir -p /var/lib/pjs
sudo python3 -m pjs --config config.json uji-mikrotik
sudo python3 -m pjs --config config.json uji-ai
sudo python3 -m pjs --config config.json jalan
```

Untuk lab, setel `learning_hours` ke `0` dan daftarkan semua VM di bagian `devices`, kecuali 10.10.0.66 yang berperan sebagai "laptop asing".

Kotak dijalankan dengan `sudo` karena berkas `eve.json` milik Suricata hanya bisa dibaca root. Ini cukup untuk lab. Untuk pemasangan sungguhan, buat pengguna khusus yang hanya diberi izin baca ke berkas itu.

Dashboard dibuka dari VM lain di jaringan kantor: `http://10.10.0.2:8080`. Supaya bisa dibuka dari laptop asli, tambahkan kartu host-only ke kotak, atau pakai port forwarding pada kartu NAT.

Setelah semua terpasang, **putuskan kartu NAT** (Settings → Network → kartu 1 → hapus centang "Cable Connected"). Kotak tetap bekerja normal. Ini bukti "mandiri" untuk video.

## 5. VM genset (sekaligus kamera)

Ubuntu Server kecil di jaringan peralatan:

```bash
sudo ip addr add 10.20.0.10/24 dev enp0s3
sudo ip addr add 10.20.0.21/24 dev enp0s3      # alamat kedua: kamera
sudo ip route add default via 10.20.0.1
sudo python3 lab/genset_tiruan.py --port 502
```

(Agar tetap setelah menyala ulang, tulis alamat ini di netplan.)

Halaman lampu ada di port 8081. Tambahkan kartu **host-only** ke VM ini supaya halaman lampu bisa dibuka dari browser laptop asli, misalnya `http://192.168.56.10:8081`.

Kalau ESP32 lampu sudah ada: colokkan ke laptop, teruskan ke VM lewat menu Devices → USB, lalu:

```bash
pip install pyserial
sudo python3 lab/genset_tiruan.py --port 502 --serial /dev/ttyUSB0
```

## 6. VM klien (laptop asing sekaligus laptop staf)

```bash
sudo ip addr add 10.10.0.66/24 dev enp0s3
sudo ip addr add 10.10.0.23/24 dev enp0s3      # alamat kedua: laptop staf
sudo ip route add default via 10.10.0.1
```

## 7. VM internet palsu

```bash
sudo ip addr add 203.0.113.50/24 dev enp0s3
sudo ip addr add 203.0.113.77/24 dev enp0s3
sudo ip route add default via 203.0.113.1
sudo python3 lab/penerima.py --port 80
```

## 8. Menjalankan empat skenario

| No | Di VM | Perintah | Yang harus terlihat di dashboard |
|---|---|---|---|
| 1 | klien | `python3 lab/serangan_genset.py --target 10.20.0.10 --dari 10.10.0.66 --ulang 5` | "Perintah asing ke Genset utama", kritis, **diisolasi otomatis**. Kiriman ke-2 dan seterusnya gagal karena sudah diblokir router |
| 2 | genset | `python3 lab/kirim_berkala.py --tujuan 203.0.113.50 --dari 10.20.0.21 --ukuran 500000 --jumlah 3 --jeda 5` | "Kamera ... mengirim data ke luar markas", tinggi, menunggu keputusan |
| 3 | klien | `python3 lab/kirim_berkala.py --tujuan 203.0.113.77 --dari 10.10.0.23 --jeda 10 --jumlah 8` | "... menghubungi alamat luar secara teratur", tinggi |
| 4 | kotak | `sudo python3 lab/ubah_catatan.py /var/lib/pjs/bukti.jsonl` lalu tekan **Periksa sekarang** | Layar merah: "Entri #… hilang" |

Untuk skenario 1, sebelum menyerang, cek dulu di MikroTik: `/ip firewall address-list print`. Sesudah serangan, alamat 10.10.0.66 muncul di daftar `pjs-karantina` dengan sisa waktu 24 jam.

## 8b. AI deteksi perilaku di lab (skenario 5)

AI deteksi perilaku perlu belajar kebiasaan normal lab lebih dulu. Ada dua pilihan:

**Pilihan 1 (disarankan): belajar dari lalu lintas lab sungguhan.**

1. Di `config.json`, setel `"learning_hours": 1` dan `"anomaly": {"window_s": 60}`.
2. Hapus folder data kotak (`/var/lib/pjs`) supaya masa belajar dimulai dari awal, lalu jalankan kotak.
3. Selama 1 jam, buat lalu lintas normal:

   ```bash
   # di VM genset (alamat pengendali 10.20.0.5 ditambahkan dulu)
   sudo ip addr add 10.20.0.5/24 dev enp0s3
   python3 lab/pengendali_tiruan.py --genset 10.20.0.10 --dari 10.20.0.5 --jeda 5
   # di VM klien, kegiatan kantor biasa ke "internet"
   python3 lab/kirim_berkala.py --tujuan 203.0.113.50 --dari 10.10.0.23 --jeda 7 --acak 0.8 --jumlah 600
   ```

   `--acak 0.8` membuat jedanya tidak teratur. Tanpa itu, kotak akan (dengan benar) menganggapnya sinyal berkala. Satu rentang 60 detik per perangkat per jaringan menghasilkan satu contoh. Model butuh 200 contoh per jaringan, jadi tambah perangkat atau perpanjang waktu belajar kalau kurang. Tanda di dashboard: "AI perilaku: belajar (… contoh)", lalu "aktif".

**Pilihan 2 (cepat, untuk latihan): pakai contoh demo.** Setel `"anomaly": {"window_s": 10, "seed_file": "lab/contoh_riwayat_normal.jsonl"}`. Contoh ini buatan dan belum tentu cocok dengan lalu lintas lab, jadi bisa muncul alarm palsu.

Setelah AI aktif, jalankan skenario 5:

```bash
# di VM genset, alamat kunci pintu ditambahkan dulu
sudo ip addr add 10.20.0.40/24 dev enp0s3
python3 lab/pindai_tiruan.py --jaringan 10.20.0 --dari 10.20.0.40
```

Yang harus terlihat: kejadian "Perilaku tidak biasa: Kunci Pintu Gudang Senjata" dengan skor keanehan dan alasannya, paling lambat satu rentang waktu setelah pemindaian.

## 9. Masalah yang sering muncul

| Gejala | Kemungkinan penyebab dan jalan keluar |
|---|---|
| `eve.json` kosong | Nama kartu di af-packet salah, atau Promiscuous Mode belum "Allow All". Cek `ip -br link` |
| Ada catatan flow tapi tidak ada peringatan Modbus | Modbus belum dinyalakan di `app-layer`, atau berkas `pjs-ot.rules` belum terdaftar. Jalankan `sudo suricata -T` |
| Peringatan muncul dua kali per serangan | Normal: paket terlihat di jaringan kantor dan peralatan. Kotak menggabungkannya menjadi satu kejadian (lihat "Terjadi 2 kali") |
| Isolasi gagal "tidak bisa dihubungi" | Layanan API MikroTik mati atau hanya menerima alamat lain. Cek `/ip service print` |
| Alamat masuk karantina tapi serangan tetap lolos | Aturan buang tidak di urutan teratas. Cek `/ip firewall filter print`, pindahkan ke nomor 0 |
| Sinyal berkala tidak muncul | Butuh minimal 6 sambungan dengan jarak sama. Pastikan `--jumlah` 8 atau lebih |
| Penjelasan selalu "bawaan" | Ollama belum jalan atau model belum diunduh. Jalankan `python3 -m pjs uji-ai` |
| Penjelasan AI lambat | Pakai model yang lebih kecil, atau tambah RAM dan CPU untuk VM kotak |
