# 01 · Jaringan dasar

Bab ini menjelaskan bagaimana komputer dan peralatan saling "berbicara". Semua bab berikutnya bergantung pada bab ini.

## 1. Jaringan itu seperti kantor pos

Bayangkan markas sebagai kompleks perumahan:

| Dunia nyata | Jaringan komputer |
|---|---|
| Rumah | Perangkat (laptop, kamera, genset) |
| Alamat rumah | **Alamat IP**, misalnya `10.20.0.10` |
| Nomor pelat motor / nomor rangka | **Alamat MAC**, misalnya `24:0a:c4:20:00:10` |
| Pintu atau loket di dalam rumah | **Port**, misalnya 502 untuk Modbus |
| Surat | **Paket** |
| Tukang pos di dalam kompleks | **Switch** |
| Kantor pos yang menghubungkan kompleks | **Router** |

Kalau laptop ingin mengirim pesan ke genset, ia memasukkan pesan ke "amplop" bertuliskan alamat pengirim dan alamat tujuan, lalu menyerahkannya ke jaringan.

## 2. Alamat IP

Alamat IP (versi 4) terdiri dari **empat angka 0–255** dipisah titik: `10.20.0.10`. Totalnya 32 bit (4 × 8 bit).

### Jaringan dan "/24"

Tulisan `10.20.0.0/24` berarti: **24 bit pertama** (tiga angka pertama, `10.20.0`) adalah nama jaringannya, dan angka terakhir adalah nomor perangkat. Jadi:

- `10.20.0.0` adalah nama jaringan (tidak dipakai perangkat),
- `10.20.0.1` sampai `10.20.0.254` bisa dipakai perangkat (254 alamat),
- `10.20.0.255` adalah alamat **siaran** (broadcast), artinya "untuk semua perangkat di jaringan ini".

Di proyek ini:

| Jaringan | Isi |
|---|---|
| `10.10.0.0/24` | Jaringan kantor (IT) |
| `10.20.0.0/24` | Jaringan peralatan (OT) |
| `203.0.113.0/24` | "Internet palsu" di lab |

Kode di `pjs/config.py` memakai pustaka `ipaddress` untuk menjawab pertanyaan seperti "apakah 10.20.0.10 ada di dalam 10.20.0.0/24?".

### Alamat privat dan alamat publik

Ada rentang alamat yang khusus untuk jaringan dalam (privat) dan tidak dipakai di internet:

- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

Alamat selain itu umumnya alamat publik di internet. Kotak menganggap alamat yang **tidak tercantum** di daftar jaringan markas sebagai "luar markas" (lihat `Config.is_external`).

## 3. Alamat MAC

Alamat MAC adalah nomor yang ditanam di kartu jaringan oleh pabrik, 6 byte, misalnya `44:19:b6:20:00:21`.

- **3 byte pertama** (`44:19:b6`) disebut **OUI** dan menunjukkan pabriknya. `44:19:b6` milik Hikvision (pembuat kamera CCTV).
- Kotak memakai ini untuk menebak merek perangkat (`pjs/vendors.py`).

Perbedaan penting: **alamat IP bisa berubah-ubah, MAC biasanya tetap.** MAC hanya terlihat di dalam satu jaringan. Begitu paket melewati router, MAC pengirim diganti MAC router. Karena itu, konfigurasi kotak punya `router_macs`: MAC router tidak boleh ditempelkan ke perangkat lain.

## 4. Port

Satu perangkat bisa menjalankan banyak layanan sekaligus. Port membedakan layanan itu, angkanya 0–65535. Beberapa yang muncul di proyek ini:

| Port | Layanan |
|---|---|
| 23 | Telnet: masuk jarak jauh tanpa enkripsi (berbahaya) |
| 53 | DNS: buku telepon nama ke alamat |
| 80 | HTTP: halaman web |
| 443 | HTTPS: halaman web terenkripsi |
| 445 | SMB: berbagi berkas Windows |
| 502 | **Modbus**: bahasa peralatan industri (genset) |
| 554 | RTSP: aliran video kamera |
| 8080 | Dashboard Pos Jaga |
| 8728 | API MikroTik |
| 11434 | Ollama (AI lokal) |

## 5. Paket dan lapisan amplop

Satu pesan dibungkus berlapis-lapis, seperti amplop di dalam amplop:

```
┌ Ethernet: MAC pengirim, MAC tujuan ───────────────────────────────┐
│ ┌ IP: alamat IP pengirim, alamat IP tujuan ─────────────────────┐ │
│ │ ┌ TCP/UDP: port pengirim, port tujuan ──────────────────────┐ │ │
│ │ │ Isi pesan (misalnya perintah Modbus "matikan coil 0")      │ │ │
│ │ └────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

Suricata membuka semua lapisan ini satu per satu untuk melihat isinya.

## 6. TCP dan UDP

- **TCP** seperti telepon: tersambung dulu, baru bicara, dan setiap kata dipastikan sampai. Sebelum bicara ada "jabat tangan tiga langkah": SYN ("halo?"), SYN-ACK ("halo, siap"), ACK ("oke"). Modbus TCP, web, dan SMB memakai TCP.
- **UDP** seperti melempar kartu pos: langsung kirim, tidak dicek sampai atau tidak. DNS biasanya memakai UDP.

Satu "percakapan" TCP dari awal sampai akhir disebut **flow** (aliran). Suricata memberi setiap flow nomor `flow_id`.

## 7. Switch, router, dan "salinan lalu lintas"

- **Switch** menyambungkan perangkat di **satu** jaringan. Ia mengantar paket hanya ke colokan tujuan (berdasarkan MAC).
- **Router** menyambungkan **beberapa** jaringan dan memutuskan rute (berdasarkan IP). Router juga bisa memasang **firewall**, yaitu aturan paket mana yang boleh lewat.

Karena switch hanya mengantar ke tujuan, kotak yang dicolokkan biasa tidak melihat percakapan perangkat lain. Solusinya **port mirror** (di Cisco disebut SPAN): switch atau router diminta **menyalin** semua lalu lintas ke satu colokan tempat kotak tersambung. Kotak hanya menerima salinan, jadi ia **pasif**: tidak mengganggu dan tidak memperlambat jaringan.

Di lab VirtualBox, fungsi ini digantikan pengaturan **Promiscuous Mode: Allow All**.

## 8. Layanan pendukung: DHCP, DNS, ARP, NAT

| Nama | Fungsi | Perumpamaan |
|---|---|---|
| DHCP | Membagikan alamat IP otomatis ke perangkat yang baru tersambung | Petugas yang memberi nomor kamar tamu |
| DNS | Mengubah nama (`server-berkas.markas.lokal`) menjadi alamat IP | Buku telepon |
| ARP | Mencari MAC dari alamat IP di jaringan yang sama | Bertanya "siapa yang tinggal di nomor 10?" |
| NAT | Router mengganti alamat privat dengan alamat publiknya saat keluar ke internet | Semua surat keluar kompleks memakai alamat kantor pos |

NAT penting untuk kotak: kalau kotak mendengar **setelah** NAT, semua lalu lintas keluar tampak berasal dari router. Karena itu, kotak harus mendengar **di dalam** jaringan markas, sebelum NAT.

## 9. Mencoba sendiri

Di Windows (Command Prompt atau PowerShell):

```bash
ipconfig /all          # alamat IP, MAC, dan gateway laptopmu
ping 8.8.8.8           # apakah bisa menjangkau alamat itu
tracert 8.8.8.8        # router mana saja yang dilewati
arp -a                 # tabel IP ke MAC yang diketahui laptopmu
nslookup google.com    # tanya DNS
```

Di Linux: `ip addr`, `ip route`, `ping`, `traceroute`, `ip neigh`, `dig`.

## Latihan

1. Cari alamat IP, MAC, dan gateway laptopmu. Tulis 3 byte pertama MAC-mu, lalu cari pabriknya di internet (kata kunci: "MAC vendor lookup").
2. Berapa alamat yang bisa dipakai perangkat di `192.168.1.0/24`? Apa alamat siarannya?
3. Buka `config.demo.json`. Perangkat mana saja yang ada di jaringan peralatan?
4. Kenapa kotak tidak boleh dipasang di luar router (setelah NAT)?

## Kamu paham kalau...

- bisa menjelaskan beda alamat IP, alamat MAC, dan port dengan perumpamaan sendiri,
- tahu kenapa switch biasa tidak memperlihatkan semua lalu lintas ke kotak, dan apa gunanya port mirror,
- bisa membaca `10.20.0.0/24` dan tahu alamat mana yang termasuk di dalamnya.
