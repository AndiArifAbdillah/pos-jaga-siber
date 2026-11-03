"""Pembuat lalu lintas lab: menghubungi satu alamat secara berkala.

Dipakai untuk dua skenario demo:
- Skenario kamera: jalankan di VM "kamera", kirim data ke "internet palsu".
- Skenario sinyal berkala: jalankan di VM "laptop staf", meniru program jahat
  yang melapor ke pengendalinya setiap beberapa detik.

Penerimanya lab/penerima.py di VM "internet palsu":
  sudo python3 lab/penerima.py --port 80

Contoh:
  python lab/kirim_berkala.py --tujuan 203.0.113.77 --jeda 20 --jumlah 10
  python lab/kirim_berkala.py --tujuan 203.0.113.50 --ukuran 500000 --jumlah 3 --dari 10.20.0.21
"""

import argparse
import http.client
import os
import random
import time


def main():
    parser = argparse.ArgumentParser(description="Lalu lintas berkala untuk lab Pos Jaga Siber")
    parser.add_argument("--tujuan", required=True, help="alamat penerima di lab")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--jeda", type=float, default=20.0, help="jeda antar sambungan (detik)")
    parser.add_argument("--jumlah", type=int, default=10)
    parser.add_argument("--ukuran", type=int, default=0, help="byte data yang dikirim (0 = hanya permintaan biasa)")
    parser.add_argument("--dari", help="alamat asal (kalau VM punya lebih dari satu alamat)")
    parser.add_argument("--acak", type=float, default=0.0,
                        help="variasi jeda, misalnya 0.8 = jeda acak 20%%-180%%. Pakai untuk lalu lintas normal, supaya tidak dianggap sinyal berkala")
    args = parser.parse_args()

    body = os.urandom(args.ukuran) if args.ukuran else None
    source = (args.dari, 0) if args.dari else None
    for n in range(1, args.jumlah + 1):
        stamp = time.strftime("%H:%M:%S")
        conn = http.client.HTTPConnection(args.tujuan, args.port, timeout=5, source_address=source)
        try:
            conn.request("POST" if body else "GET", "/lapor", body=body)
            status = conn.getresponse().status
            print(f"{stamp}  sambungan {n}: terkirim (balasan {status})")
        except OSError as exc:
            print(f"{stamp}  sambungan {n}: gagal ({exc})")
        finally:
            conn.close()
        if n < args.jumlah:
            time.sleep(args.jeda * random.uniform(1 - args.acak, 1 + args.acak))


if __name__ == "__main__":
    main()
