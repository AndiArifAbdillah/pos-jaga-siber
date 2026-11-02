"""Demo skenario "jejak": mengubah catatan bukti untuk menunjukkan bahwa perubahan langsung ketahuan.

Meniru orang yang ingin menghapus jejak. Salinan asli disimpan dulu
dengan akhiran .cadangan, jadi demo bisa diulang.

Contoh:
  python lab/ubah_catatan.py                      # hapus satu entri di tengah
  python lab/ubah_catatan.py --ubah 5             # ganti isi entri #5 tanpa menghapusnya
  python lab/ubah_catatan.py --pulihkan           # kembalikan dari cadangan
Setelah itu tekan "Periksa sekarang" di dashboard, atau: python -m pjs --config config.demo.json periksa

Matikan kotak dulu sebelum --pulihkan. Kalau kotak masih menyala, entri yang
ditulis setelah pengubahan ikut hilang dan rantai tetap putus. Cara paling
mudah mengulang demo dari nol: python -m pjs demo --putar --baru
"""

import argparse
import json
import shutil
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "data-demo" / "bukti.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Ubah catatan bukti untuk demo")
    parser.add_argument("berkas", nargs="?", default=str(DEFAULT))
    parser.add_argument("--hapus", type=int, help="nomor entri yang dihapus")
    parser.add_argument("--ubah", type=int, help="nomor entri yang isinya diganti")
    parser.add_argument("--pulihkan", action="store_true", help="kembalikan dari cadangan")
    args = parser.parse_args()

    path = Path(args.berkas)
    backup = path.with_name(path.name + ".cadangan")
    if args.pulihkan:
        shutil.copyfile(backup, path)
        print(f"Dipulihkan dari {backup}")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3:
        raise SystemExit("Catatan terlalu pendek. Jalankan demo dulu supaya ada beberapa entri.")
    shutil.copyfile(path, backup)
    entries = [json.loads(line) for line in lines]

    if args.ubah:
        for entry in entries:
            if entry["seq"] == args.ubah:
                entry["data"]["operator"] = "orang lain"
                entry["data"]["diubah"] = True
                print(f"Isi entri #{args.ubah} diganti (hash dan tanda tangan dibiarkan).")
                break
        else:
            raise SystemExit(f"Entri #{args.ubah} tidak ada.")
    else:
        target = args.hapus or entries[len(entries) // 2]["seq"]
        before = len(entries)
        entries = [e for e in entries if e["seq"] != target]
        if len(entries) == before:
            raise SystemExit(f"Entri #{target} tidak ada.")
        print(f"Entri #{target} dihapus dari catatan.")

    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")
    print(f"Cadangan asli: {backup}")


if __name__ == "__main__":
    main()
