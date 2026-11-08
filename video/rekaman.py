"""Memakai rekaman suara sendiri sebagai narasi video.

Alur:
  1. `python video/rekaman.py naskah` menulis naskah-rekaman.md: semua kalimat
     bernomor, lengkap dengan arahan gaya baca per adegan.
  2. Rekam naskah itu: satu berkas panjang (atau beberapa berkas berurutan),
     diam sekitar 2 detik di antara kalimat. Kalimat yang salah cukup diulang.
  3. `python video/rekaman.py cek rekaman.m4a` membersihkan suara, memotongnya
     per kalimat, lalu mencocokkan potongan dengan kalimat naskah. Hasilnya
     berupa tabel untuk diperiksa. Belum ada video yang dirender.
  4. `python video/buat_video.py --rekaman rekaman.m4a` membuat videonya.
     Waktu animasi mengikuti panjang setiap kalimat yang kamu ucapkan.

Pencocokan memakai panjang ucapan: setiap kalimat dibandingkan dengan perkiraan
panjangnya (dari suara buatan). Potongan yang tidak cocok, misalnya kalimat yang
diulang karena salah atau suara batuk, dilewati. Kalau ada ulangan, yang dipakai
adalah yang terakhir. Hasil pencocokan disimpan di kerja/rekaman/pemetaan-otomatis.json.
Kalau ada yang keliru, salin berkas itu menjadi pemetaan.json lalu ubah angka
detiknya; pemetaan.json selalu didahulukan.
"""

import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FOLDER = HERE / "kerja" / "rekaman"
RATE = 48000
ANALISIS = 16000
JEDA_ANTAR_BERKAS = 2.5

# Pembersihan suara: buang dengung rendah dan kurangi desis latar. Keras-lembut
# suara tidak diratakan (tanpa kompresor), supaya ekspresi bicara tetap utuh.
# Kekerasan suara keseluruhan disamakan ke -16 LUFS dengan satu penguatan tetap,
# dan hanya puncak yang terlalu keras yang ditahan pembatas.
BERSIH = "highpass=f=80,afftdn=nr=12:nf=-50:tn=1"
TARGET_LUFS = -16.0


def kekerasan(path):
    """Kekerasan rata-rata rekaman (LUFS) setelah dibersihkan."""
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af", BERSIH + ",loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, errors="replace").stderr
    data = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    return float(data["input_i"])


def ucapan_manusia(k):
    """Kalimat yang dibaca orang: versi 'ucap' kalau ada (angka sudah ditulis dengan huruf)."""
    return k.get("ucap", k["teks"]).replace("O I S F", "O-I-S-F")


def tulis_naskah(naskah, path):
    baris = [
        "# Naskah rekaman suara: video Pos Jaga Siber",
        "",
        f"Ada {sum(len(a['ketukan']) for a in naskah['adegan'])} kalimat, sekitar 5–6 menit kalau dibaca. Nomor kalimat **tidak** ikut dibaca.",
        "",
        "## Cara merekam",
        "",
        "1. Cari kamar yang sunyi dan banyak kain (kasur, lemari baju, gorden). Matikan kipas dan AC. Aktifkan mode pesawat.",
        "2. Pegang HP sekitar 15–20 cm dari mulut, agak menyamping supaya bunyi \"p\" dan \"b\" tidak meletup. Rekam sambil berdiri.",
        "3. Rekam dengan aplikasi perekam suara bawaan HP. Boleh satu rekaman panjang, boleh juga satu rekaman per adegan.",
        "4. **Diam sekitar 2 detik di antara kalimat.** Tarik napas dan hitung \"satu, dua\" dalam hati.",
        "5. **Kalau salah, diam 2 detik, lalu ulangi kalimat itu dari awal.** Tidak perlu menghentikan rekaman. Yang dipakai adalah ulangan terakhir.",
        "6. Baca seperti bercerita ke teman, bukan membaca teks. Senyum saat bicara: senyum terdengar di suara. Ikuti arahan di setiap adegan.",
        "7. \"AI\" dibaca **ei-ai**. Istilah Inggris (machine learning, Isolation Forest, dashboard) dibaca biasa dalam bahasa Inggris.",
        "",
        "Waktu animasi di video akan mengikuti kecepatan bicaramu, jadi tidak perlu terburu-buru dan tidak perlu menonton videonya saat merekam.",
        "",
    ]
    n = 0
    for i, adegan in enumerate(naskah["adegan"], 1):
        judul = adegan["bab"].split("·", 1)[-1].strip() if adegan["bab"] else "Pembuka"
        baris += [f"## Adegan {i}: {judul}", "", f"*Arahan: {adegan.get('arahan', '')}*", ""]
        for k in adegan["ketukan"]:
            n += 1
            baris.append(f"{n}. {ucapan_manusia(k)}")
        baris.append("")
    path.write_text("\n".join(baris), encoding="utf-8")
    return n


def bersihkan(files, out):
    """Satukan berkas rekaman (berurutan) menjadi satu wav bersih 48 kHz mono."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, f in enumerate(files):
        part = FOLDER / f"_bagian{i}.wav"
        gain = max(-20.0, min(30.0, TARGET_LUFS - kekerasan(f)))
        filt = f"{BERSIH},volume={gain:.2f}dB,alimiter=limit=0.84:level=0"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-af", filt, "-ar", str(RATE), "-ac", "1",
                        "-sample_fmt", "s16", str(part)], check=True)
        parts.append(part)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        for i, part in enumerate(parts):
            if i:
                w.writeframes(b"\0\0" * int(JEDA_ANTAR_BERKAS * RATE))
            with wave.open(str(part), "rb") as r:
                while True:
                    data = r.readframes(RATE * 5)
                    if not data:
                        break
                    w.writeframes(data)
            part.unlink()


def energi(path, frame_s=0.02):
    """Kekerasan suara (dB) setiap 20 ms. Dibaca bertahap supaya hemat memori."""
    tmp = FOLDER / "_analisis.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ar", str(ANALISIS), "-ac", "1", "-sample_fmt", "s16", str(tmp)], check=True)
    step = int(frame_s * ANALISIS)
    out = []
    with wave.open(str(tmp), "rb") as r:
        while True:
            data = r.readframes(step * 500)
            if not data:
                break
            x = np.frombuffer(data, np.int16).astype(np.float32) / 32768
            k = len(x) // step
            if k:
                fr = x[:k * step].reshape(k, step)
                out.append(20 * np.log10(np.sqrt((fr * fr).mean(axis=1)) + 1e-9))
    tmp.unlink()
    return np.concatenate(out), frame_s


def potong(db, frame_s, jeda_pisah):
    """Bagian bersuara, dipisah oleh diam yang lebih panjang dari jeda_pisah detik."""
    lantai, puncak = np.percentile(db, 10), np.percentile(db, 97)
    batas = max(lantai + 10, puncak - 32)
    aktif = db > batas
    # hilangkan bunyi pendek (klik, napas) dan isi lubang pendek di tengah kata
    segs, mulai = [], None
    for i, a in enumerate(np.append(aktif, False)):
        if a and mulai is None:
            mulai = i
        elif not a and mulai is not None:
            segs.append([mulai * frame_s, i * frame_s])
            mulai = None
    gabung = []
    for s in segs:
        if gabung and s[0] - gabung[-1][1] < jeda_pisah:
            gabung[-1][1] = s[1]
        else:
            gabung.append(s)
    return [s for s in gabung if s[1] - s[0] >= 0.3]


def cocokkan(segs, perkiraan):
    """Pasangkan potongan dengan kalimat naskah berdasarkan panjangnya (pemrograman dinamis).

    Setiap kalimat memakai 1–3 potongan berurutan (kalimat dengan jeda di tengah).
    Potongan di antaranya boleh dilewati (ulangan, batuk). Melewati potongan yang
    mirip kalimat berikutnya lebih murah, sehingga ulangan terakhir yang dipakai.
    """
    n, m = len(perkiraan), len(segs)
    dur = lambda a, b: segs[b][1] - segs[a][0]
    LEWAT, GABUNG, SIGMA = 1.2, 0.35, 0.28
    rasio = sum(s[1] - s[0] for s in segs) / sum(perkiraan)
    for _ in range(3):
        INF = float("inf")
        best = [[INF] * (m + 1) for _ in range(n + 1)]
        asal = [[None] * (m + 1) for _ in range(n + 1)]
        best[0][0] = 0.0
        for i in range(1, n + 1):
            harap = perkiraan[i - 1] * rasio
            for j in range(1, m + 1):  # kalimat i berakhir di potongan j-1
                for g in range(1, 4):  # jumlah potongan untuk kalimat ini
                    a = j - g
                    if a < 0:
                        break
                    # jeda di tengah kalimat wajar sampai sekitar 1,2 detik; lebih dari itu
                    # kemungkinan besar bunyi lain (batuk, ulangan) yang ikut tergabung
                    jeda_dalam = sum(max(0.0, segs[s + 1][0] - segs[s][1] - 1.2) for s in range(a, j - 1))
                    biaya_cocok = (math.log(dur(a, j - 1) / harap) / SIGMA) ** 2 + GABUNG * (g - 1) + 2.0 * jeda_dalam
                    for p in range(a, max(-1, a - 6), -1):  # potongan p..a-1 dilewati
                        if best[i - 1][p] == INF:
                            continue
                        lewat = 0.0
                        for s in range(p, a):
                            mirip = (math.log((segs[s][1] - segs[s][0]) / harap) / SIGMA) ** 2
                            lewat += LEWAT - 0.6 * math.exp(-mirip / 2)
                        c = best[i - 1][p] + lewat + biaya_cocok
                        if c < best[i][j]:
                            best[i][j], asal[i][j] = c, (p, a)
        akhir = min(range(1, m + 1), key=lambda j: best[n][j] + LEWAT * (m - j))
        if best[n][akhir] == INF:
            return None
        hasil, j = [], akhir
        for i in range(n, 0, -1):
            p, a = asal[i][j]
            hasil.append((a, j - 1))
            j = p
        hasil.reverse()
        rasio = sum(dur(a, b) for a, b in hasil) / sum(perkiraan)
    return hasil


def siapkan(files, perkiraan, teks):
    """Proses rekaman. Hasil: (daftar wav per kalimat, baris laporan)."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    bersih = FOLDER / "rekaman-bersih.wav"
    bersihkan(files, bersih)
    manual = FOLDER / "pemetaan.json"
    laporan = []
    if manual.exists():
        rentang = json.loads(manual.read_text(encoding="utf-8"))
        laporan.append(f"Memakai pemetaan buatan sendiri: {manual}")
        dilewati = []
    else:
        db, frame_s = energi(bersih)
        hasil = segs = None
        for jeda in (1.1, 0.85, 0.65, 0.5):
            segs = potong(db, frame_s, jeda)
            if len(segs) >= len(perkiraan):
                hasil = cocokkan(segs, perkiraan)
                if hasil:
                    break
        if not hasil:
            raise SystemExit(f"Rekaman hanya terpotong menjadi {len(segs)} bagian, padahal naskah punya {len(perkiraan)} kalimat. "
                             "Pastikan ada jeda diam sekitar 2 detik di antara kalimat.")
        rentang = [[round(segs[a][0], 2), round(segs[b][1], 2)] for a, b in hasil]
        dipakai = {i for a, b in hasil for i in range(a, b + 1)}
        dilewati = [segs[i] for i in range(len(segs)) if i not in dipakai]
        (FOLDER / "pemetaan-otomatis.json").write_text(json.dumps(rentang, indent=1), encoding="utf-8")
    if len(rentang) != len(perkiraan):
        raise SystemExit(f"pemetaan.json berisi {len(rentang)} rentang, padahal naskah punya {len(perkiraan)} kalimat.")
    total_ucap = sum(b - a for a, b in rentang)
    rasio = total_ucap / sum(perkiraan)
    wavs = []
    for i, ((a, b), harap) in enumerate(zip(rentang, perkiraan), 1):
        out = FOLDER / f"kalimat-{i:02d}.wav"
        mulai, panjang = max(0.0, a - 0.08), (b + 0.18) - max(0.0, a - 0.08)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mulai:.3f}", "-t", f"{panjang:.3f}", "-i", str(bersih),
                        "-af", f"afade=t=in:d=0.03,afade=t=out:st={max(0.0, panjang - 0.08):.3f}:d=0.08",
                        "-ar", str(RATE), "-ac", "1", "-sample_fmt", "s16", str(out)], check=True)
        wavs.append(out)
        r = (b - a) / (harap * rasio)
        tanda = "  <- periksa" if abs(math.log(r)) > 0.45 else ""
        laporan.append(f"{i:2d}. {a:7.2f}-{b:7.2f} dtk ({b - a:4.1f} dtk, {r:4.2f}x perkiraan){tanda}  {teks[i - 1][:60]}")
    if dilewati:
        laporan.append("Bagian rekaman yang dilewati (ulangan, batuk, atau bunyi lain): " +
                       ", ".join(f"{a:.1f}-{b:.1f} dtk" for a, b in dilewati))
    laporan.append(f"Kecepatan bicara: {1 / rasio:.2f}x suara buatan. Rekaman bersih: {bersih}")
    return wavs, laporan


def perkiraan_dan_teks(naskah):
    sys.path.insert(0, str(HERE))
    from buat_video import lafalkan, suara
    perk, teks = [], []
    for adegan in naskah["adegan"]:
        for k in adegan["ketukan"]:
            perk.append(suara(lafalkan(k.get("ucap", k["teks"]), naskah), naskah["suara"], naskah["kecepatan"])[1])
            teks.append(k["teks"])
    return perk, teks


def main():
    naskah = json.loads((HERE / "naskah.json").read_text(encoding="utf-8"))
    if len(sys.argv) >= 2 and sys.argv[1] == "naskah":
        out = HERE / "naskah-rekaman.md"
        print(f"{tulis_naskah(naskah, out)} kalimat ditulis ke {out}")
        return 0
    if len(sys.argv) >= 3 and sys.argv[1] == "cek":
        perk, teks = perkiraan_dan_teks(naskah)
        _, laporan = siapkan([Path(f) for f in sys.argv[2:]], perk, teks)
        print("\n".join(laporan))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
