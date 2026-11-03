"""Membuat contoh perilaku normal untuk demo AI deteksi perilaku.

Di markas sungguhan, kotak mempelajari perilaku normal sendiri selama masa
belajar (bawaan 14 hari). Untuk demo di satu laptop tidak ada waktu belajar,
jadi model dilatih dari contoh buatan ini. Setiap baris adalah ringkasan satu
rentang waktu (10 detik, sama dengan window_s di config.demo.json) dari satu
perangkat, mengikuti pola perangkat di lab demo.

Hasilnya selalu sama (memakai benih acak tetap), sehingga demo bisa diulang.

  python lab/buat_riwayat_normal.py
"""

import argparse
import json
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "contoh_riwayat_normal.jsonl"


def log_uniform(rng, low, high):
    return int(math.exp(rng.uniform(math.log(low), math.log(high))))


def ot_window(rng):
    pick = rng.random()
    if pick < 0.4:  # PC pengendali membaca genset dan kunci pintu
        flows = rng.randint(1, 4)
        return {"flows": flows, "destinations": rng.randint(1, min(2, flows)), "ports": rng.randint(1, min(2, flows)),
                "bytes_out": rng.randint(500, 4000), "bytes_in": rng.randint(500, 5000), "external": 0}
    if pick < 0.85:  # kamera mengirim video ke perekam CCTV
        return {"flows": rng.randint(1, 2), "destinations": 1, "ports": 1,
                "bytes_out": rng.randint(600_000, 1_600_000), "bytes_in": rng.randint(5_000, 20_000), "external": 0}
    # genset atau kunci pintu mengirim kabar singkat
    return {"flows": 1, "destinations": 1, "ports": 1,
            "bytes_out": rng.randint(200, 2000), "bytes_in": rng.randint(200, 3000), "external": 0}


def it_window(rng):
    flows = rng.randint(1, 20)
    external = 0 if rng.random() < 0.4 else rng.randint(1, min(flows, 15))
    return {"flows": flows, "destinations": rng.randint(1, min(flows, 12)), "ports": rng.randint(1, min(flows, 3)),
            "bytes_out": log_uniform(rng, 1_000, 200_000), "bytes_in": log_uniform(rng, 1_000, 5_000_000),
            "external": external}


def main():
    parser = argparse.ArgumentParser(description="Buat contoh perilaku normal untuk demo")
    parser.add_argument("--jumlah", type=int, default=400, help="jumlah contoh per jaringan")
    parser.add_argument("--ke", default=str(OUT))
    args = parser.parse_args()

    rng = random.Random(2026)
    lines = ["# Contoh perilaku normal (buatan) untuk demo AI deteksi perilaku. Dibuat oleh lab/buat_riwayat_normal.py"]
    for zone, make in (("ot", ot_window), ("it", it_window)):
        for _ in range(args.jumlah):
            feats = make(rng)
            feats["hour"] = rng.randint(0, 23)
            lines.append(json.dumps({"zone": zone, "f": feats}))
    Path(args.ke).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines) - 1} contoh ditulis ke {args.ke}")


if __name__ == "__main__":
    main()
