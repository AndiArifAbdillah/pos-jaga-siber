"""Simulasi perangkat yang dikuasai penyerang lalu memindai jaringan peralatan.

HANYA untuk lab milik tim sendiri. Skrip ini mencoba membuka sambungan ke
beberapa alamat dan port di jaringan lab, seperti perangkat yang sudah
dikuasai penyerang dan sedang mencari sasaran berikutnya.

Tidak ada aturan Suricata PJS yang khusus menangkap pola ini. Yang
diharapkan menangkapnya adalah AI deteksi perilaku (skenario 5).

Contoh (di VM genset, alamat kunci pintu 10.20.0.40 sebagai alamat tambahan):
  python3 lab/pindai_tiruan.py --jaringan 10.20.0 --dari 10.20.0.40
"""

import argparse
import socket
import time


def main():
    parser = argparse.ArgumentParser(description="Simulasi pemindaian di lab sendiri")
    parser.add_argument("--jaringan", default="10.20.0", help="tiga angka awal jaringan lab")
    parser.add_argument("--awal", type=int, default=1)
    parser.add_argument("--akhir", type=int, default=30)
    parser.add_argument("--port", default="80,443,502,554", help="daftar port, dipisah koma")
    parser.add_argument("--dari", help="alamat asal (kalau VM punya lebih dari satu alamat)")
    args = parser.parse_args()

    if not args.jaringan.startswith(("10.", "192.168.", "172.")):
        raise SystemExit("Hanya untuk jaringan lab privat (10.x, 172.16-31.x, 192.168.x).")
    ports = [int(p) for p in args.port.split(",")]
    source = (args.dari, 0) if args.dari else None
    tried = opened = 0
    started = time.time()
    for last in range(args.awal, args.akhir + 1):
        host = f"{args.jaringan}.{last}"
        for port in ports:
            tried += 1
            try:
                with socket.create_connection((host, port), timeout=0.3, source_address=source):
                    opened += 1
                    print(f"  {host}:{port} terbuka")
            except OSError:
                pass
    print(f"Selesai dalam {time.time() - started:.1f} detik: {tried} percobaan, {opened} terbuka.")


if __name__ == "__main__":
    main()
