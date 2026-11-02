# Pengaturan MikroTik untuk Pos Jaga Siber (tempel di Terminal Winbox atau SSH).
# Penjelasan: docs/belajar/05-mikrotik-dan-blokir.md
# Sesuaikan alamat 10.10.0.2 (kotak) dan sandi sebelum dipakai.

# 1. Kelompok pengguna khusus kotak: hanya boleh lewat API dan mengubah pengaturan.
/user group add name=pjs-api policy=api,read,write

# 2. Akun kotak, hanya boleh masuk dari alamat kotak.
/user add name=pjs group=pjs-api address=10.10.0.2/32 password=GANTI-DENGAN-SANDI-KUAT

# 3. Layanan API hanya menerima sambungan dari kotak.
/ip service set api address=10.10.0.2/32 disabled=no

# 4. Aturan buang untuk daftar karantina. place-before=0 = taruh paling atas,
#    supaya berlaku sebelum aturan lain (termasuk fasttrack).
#    Kalau daftar firewall filter masih kosong (biasa di MikroTik CHR baru),
#    hapus "place-before=0" dari baris pertama.
/ip firewall filter add chain=forward src-address-list=pjs-karantina action=drop comment="PJS: karantina keluar" place-before=0
/ip firewall filter add chain=forward dst-address-list=pjs-karantina action=drop comment="PJS: karantina masuk" place-before=0

# Lihat isi karantina kapan saja:
#   /ip firewall address-list print where list=pjs-karantina
# Lepas manual satu alamat:
#   /ip firewall address-list remove [find list=pjs-karantina address=10.10.0.66]
