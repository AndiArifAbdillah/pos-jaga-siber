"""PC pengendali tiruan: membaca keadaan genset secara berkala lewat Modbus.

Ini lalu lintas peralatan yang NORMAL. Jalankan selama masa belajar di lab,
supaya AI deteksi perilaku punya contoh kebiasaan jaringan peralatan.

Contoh (di VM genset, alamat pengendali 10.20.0.5 sebagai alamat tambahan):
  python3 lab/pengendali_tiruan.py --genset 10.20.0.10 --dari 10.20.0.5 --jeda 5
"""

import argparse
import socket
import struct
import time


def read_registers(host, port, source, transaction_id):
    request = struct.pack(">HHHBBHH", transaction_id % 65536, 0, 6, 1, 3, 0, 3)
    with socket.create_connection((host, port), timeout=3, source_address=source) as sock:
        sock.sendall(request)
        reply = sock.recv(256)
    if len(reply) < 15:
        return None
    return struct.unpack(">HHH", reply[9:15])


def main():
    parser = argparse.ArgumentParser(description="PC pengendali tiruan (lalu lintas Modbus normal)")
    parser.add_argument("--genset", required=True)
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--jeda", type=float, default=5.0)
    parser.add_argument("--dari", help="alamat asal (kalau VM punya lebih dari satu alamat)")
    args = parser.parse_args()

    source = (args.dari, 0) if args.dari else None
    n = 0
    while True:
        n += 1
        try:
            values = read_registers(args.genset, args.port, source, n)
            if values:
                print(f"{time.strftime('%H:%M:%S')}  genset {values[0]} V, {values[1]} Hz, bahan bakar {values[2]}%")
        except OSError as exc:
            print(f"{time.strftime('%H:%M:%S')}  gagal membaca genset: {exc}")
        time.sleep(args.jeda)


if __name__ == "__main__":
    main()
