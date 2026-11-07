"""Membuat video Pos Jaga Siber dari naskah, gambar dashboard asli, dan panggung animasi.

Urutan kerja:
  1. Suara: setiap ketukan naskah dibacakan suara bahasa Indonesia (edge-tts).
  2. Waktu: panjang suara menentukan kapan setiap ketukan dan adegan dimulai.
  3. Gambar: adegan.html diputar frame demi frame di Edge tanpa layar, lalu
     setiap frame dipotret (1920x1080, 25 frame per detik).
  4. Gabung: frame menjadi video H.264, ditambah suara narasi dan berkas teks .srt.

Butuh: ffmpeg, Microsoft Edge, pustaka playwright dan edge-tts, serta gambar dari
rekam_dashboard.py. Suara dibuat lewat layanan Microsoft (butuh internet); yang
dikirim hanya teks naskah.

Contoh:
  python video/buat_video.py --pratinjau          # beberapa gambar contoh per adegan, cepat
  python video/buat_video.py --adegan solusi      # satu adegan saja
  python video/buat_video.py                      # video lengkap
"""

import argparse
import asyncio
import hashlib
import json
import math
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE / "kerja"
SUARA = WORK / "suara"
HASIL = HERE / "hasil"
RATE = 48000
FPS = 25


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


async def _tts(text, voice, rate, mp3):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(str(mp3))


def suara(text, voice, rate):
    """Buat (atau ambil dari simpanan) berkas suara untuk satu ketukan. Hasil: (wav, durasi)."""
    SUARA.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    mp3, wav = SUARA / f"{key}.mp3", SUARA / f"{key}.wav"
    if not wav.exists():
        for attempt in range(3):
            try:
                asyncio.run(_tts(text, voice, rate, mp3))
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", str(RATE), "-ac", "1", str(wav)], check=True)
    return wav, ffprobe_duration(wav)


def lafalkan(text, naskah):
    """Ganti istilah dengan tulisan sesuai bunyinya, supaya diucapkan benar oleh suara narasi.

    'lafal.semua' dipakai untuk semua suara (misalnya AI dibaca "Ei-Ai").
    'lafal.suara_indonesia' hanya untuk suara id-ID: suara itu membaca kata Inggris
    dengan ejaan Indonesia, jadi "machine learning" perlu ditulis "masyin lerning".
    Suara multibahasa sudah bisa membaca kata Inggris, jadi tidak perlu.
    """
    lafal = naskah.get("lafal", {})
    kamus = dict(lafal.get("semua", {}))
    if naskah["suara"].startswith("id-ID"):
        kamus.update(lafal.get("suara_indonesia", {}))
    for istilah in sorted(kamus, key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(istilah)}(?!\w)", kamus[istilah], text)
    return text


def susun_waktu(naskah):
    """Hitung waktu mulai setiap ketukan dan panjang setiap adegan."""
    scenes, offset = [], 0.0
    for i, adegan in enumerate(naskah["adegan"]):
        t = 1.2 if i == 0 else 0.5
        beats = []
        for k in adegan["ketukan"]:
            wav, dur = suara(lafalkan(k.get("ucap", k["teks"]), naskah), naskah["suara"], naskah["kecepatan"])
            beats.append({"mulai": round(t, 3), "selesai": round(t + dur, 3), "teks": k["teks"], "wav": str(wav)})
            t += dur + k.get("jeda", 0.3)
        scenes.append({"id": adegan["id"], "bab": adegan["bab"], "D": round(t, 3), "offset": round(offset, 3), "ketukan": beats})
        offset += t
    for s in scenes:
        s["total"] = round(offset, 3)
    scenes[0]["awal"] = True
    scenes[-1]["akhir"] = True
    return scenes


def tulis_narasi(scenes, path):
    total = scenes[-1]["offset"] + scenes[-1]["D"]
    buf = bytearray(int(math.ceil(total * FPS) / FPS * RATE + RATE) * 2)
    for s in scenes:
        for k in s["ketukan"]:
            with wave.open(k["wav"], "rb") as w:
                data = w.readframes(w.getnframes())
            start = int(round((s["offset"] + k["mulai"]) * RATE)) * 2
            buf[start:start + len(data)] = data
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(buf))


def tulis_srt(scenes, path):
    def stamp(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines, n = [], 1
    for s in scenes:
        for k in s["ketukan"]:
            lines += [str(n), f"{stamp(s['offset'] + k['mulai'])} --> {stamp(s['offset'] + k['selesai'] + .2)}", k["teks"], ""]
            n += 1
    path.write_text("\n".join(lines), encoding="utf-8")


def bahan():
    folder = HERE / "bahan"
    status = json.loads((folder / "status.json").read_text(encoding="utf-8"))
    return {
        "kotak": json.loads((folder / "kotak.json").read_text(encoding="utf-8")),
        "bahan": {
            "perintah": "python lab/serangan_genset.py --target 127.0.0.1 --port 5022",
            "keluaran": (folder / "serangan.txt").read_text(encoding="utf-8").strip(),
            "kode": status["evidence"]["code"],
            "hilang": status["evidence"]["integrity"]["broken_at"] or 9,
        },
    }


def data_adegan(scene, extra):
    return {**scene, "b": [k["mulai"] for k in scene["ketukan"]], **extra}


def bagian_utuh(seg, durasi):
    """Bagian adegan yang sudah dirender lengkap (dipakai --lanjut)."""
    try:
        return seg.exists() and abs(ffprobe_duration(seg) - math.ceil(durasi * FPS) / FPS) < 0.1
    except subprocess.CalledProcessError:
        return False


def render(scenes, extra, only=None, preview=False, resume=False):
    from playwright.sync_api import sync_playwright

    url = (HERE / "adegan.html").as_uri()
    segments = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        for scene in scenes:
            if only and scene["id"] not in only:
                continue
            data = data_adegan(scene, extra)
            page.evaluate("d => siapkan(d)", data)
            if preview:
                times = [k["mulai"] + 2.5 for k in scene["ketukan"]] + [scene["D"] - .6]
                out = WORK / "pratinjau"
                out.mkdir(parents=True, exist_ok=True)
                for i, t in enumerate(times):
                    page.evaluate(f"seek({t})")
                    page.screenshot(path=str(out / f"{scene['id']}-{i}.png"))
                print(f"  pratinjau {scene['id']}: {len(times)} gambar")
                continue
            frames = int(math.ceil(scene["D"] * FPS))
            seg = WORK / f"bagian-{scene['id']}.mp4"
            if resume and bagian_utuh(seg, scene["D"]):
                print(f"  adegan {scene['id']}: sudah ada, dilewati")
                segments.append(seg)
                continue
            enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(seg)],
                                   stdin=subprocess.PIPE)
            started = time.time()
            for i in range(frames):
                page.evaluate(f"seek({i / FPS})")
                enc.stdin.write(page.screenshot(type="jpeg", quality=94))
            enc.stdin.close()
            enc.wait()
            print(f"  adegan {scene['id']}: {frames} frame dalam {time.time() - started:.0f} detik")
            segments.append(seg)
        browser.close()
    return segments


def main():
    parser = argparse.ArgumentParser(description="Buat video Pos Jaga Siber")
    parser.add_argument("--pratinjau", action="store_true", help="hanya gambar contoh per adegan")
    parser.add_argument("--adegan", nargs="*", help="hanya adegan tertentu")
    parser.add_argument("--lanjut", action="store_true", help="pakai bagian adegan yang sudah selesai dirender")
    args = parser.parse_args()

    WORK.mkdir(parents=True, exist_ok=True)
    HASIL.mkdir(parents=True, exist_ok=True)
    naskah = json.loads((HERE / "naskah.json").read_text(encoding="utf-8"))
    print("Menyiapkan suara narasi...")
    scenes = susun_waktu(naskah)
    total = scenes[-1]["offset"] + scenes[-1]["D"]
    print(f"Panjang video: {int(total // 60)} menit {total % 60:.0f} detik")
    (WORK / "waktu.json").write_text(json.dumps(scenes, ensure_ascii=False, indent=1), encoding="utf-8")
    extra = bahan()

    if args.pratinjau:
        render(scenes, extra, only=args.adegan, preview=True)
        print("Pratinjau di", WORK / "pratinjau")
        return 0

    segments = render(scenes, extra, only=args.adegan, resume=args.lanjut)
    if args.adegan:
        print("Bagian adegan selesai:", ", ".join(str(s) for s in segments))
        return 0

    daftar = WORK / "daftar.txt"
    daftar.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    gambar = WORK / "gambar.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(daftar), "-c", "copy", str(gambar)], check=True)
    narasi = WORK / "narasi.wav"
    tulis_narasi(scenes, narasi)
    keluaran = HASIL / "pos-jaga-siber.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(gambar), "-i", str(narasi), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest", "-movflags", "+faststart", str(keluaran)], check=True)
    tulis_srt(scenes, HASIL / "pos-jaga-siber.srt")
    print("Selesai:", keluaran)
    return 0


if __name__ == "__main__":
    sys.exit(main())
