"""Narasi dengan suara AI Google Gemini (yang dipakai di Google AI Studio).

Butuh kunci API dari Google AI Studio (aistudio.google.com, menu "Get API key").
Simpan kunci di variabel lingkungan GEMINI_API_KEY. Di Windows, jalankan sekali
di PowerShell (ganti KUNCI dengan kunci milikmu):

    [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "KUNCI", "User")

Kalau kunci sudah ada di berkas pengaturan lain (JSON dengan "gemini_api_key"),
tunjuk berkasnya lewat GEMINI_KEY_FILE, misalnya:

    GEMINI_KEY_FILE=path/ke/settings.json python video/suara_gemini.py contoh

Kunci tidak pernah ditulis ke berkas proyek atau ke layar. Yang dikirim ke Google
hanya kalimat naskah dan petunjuk gaya baca.

Pemakaian:
    python video/suara_gemini.py contoh          # contoh beberapa suara untuk dipilih
    python video/buat_video.py                   # kalau "mesin" di naskah.json = "gemini"
"""

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUARA = HERE / "kerja" / "suara"
API = "https://generativelanguage.googleapis.com/v1beta"
RATE = 48000
MODEL_CADANGAN = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]
_cara = {"mode": None}  # "interactions" atau "generate", ditentukan saat permintaan pertama berhasil


def _kunci_dari_berkas(path):
    """Kunci dari berkas pengaturan: JSON (gemini_api_key / GEMINI_API_KEY / api_key) atau teks biasa."""
    teks = Path(path).read_text(encoding="utf-8-sig").strip()
    try:
        data = json.loads(teks)
    except json.JSONDecodeError:
        return teks
    for nama in ("gemini_api_key", "GEMINI_API_KEY", "api_key"):
        if isinstance(data, dict) and data.get(nama):
            return data[nama]
    return None


def _asli(k):
    """Abaikan tulisan contoh seperti "KUNCI" atau "ISI_API_KEY_DI_SINI"."""
    return k if k and k.strip() and k.strip().upper() not in ("KUNCI", "KEY") and not k.strip().upper().startswith("ISI_") else None


def kunci():
    k = None
    if os.environ.get("GEMINI_KEY_FILE"):  # berkas yang ditunjuk langsung didahulukan
        k = _asli(_kunci_dari_berkas(os.environ["GEMINI_KEY_FILE"]))
    k = k or _asli(os.environ.get("GEMINI_API_KEY")) or _asli(os.environ.get("GOOGLE_API_KEY"))
    if not k and sys.platform == "win32":
        # variabel yang baru disetel lewat PowerShell belum terlihat oleh proses yang sudah berjalan
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                k = _asli(winreg.QueryValueEx(reg, "GEMINI_API_KEY")[0])
        except OSError:
            k = None
    if not k:
        raise SystemExit("Kunci API Gemini belum ada. Buat di aistudio.google.com (Get API key), lalu simpan sebagai "
                         "GEMINI_API_KEY. Lihat petunjuk di bagian atas video/suara_gemini.py.")
    return k.strip()


def _kirim(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": kunci()})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def _cari_audio(obj):
    """Ambil data audio base64 dari jawaban, apa pun bentuk JSON-nya."""
    if isinstance(obj, dict):
        if "inlineData" in obj and isinstance(obj["inlineData"], dict) and obj["inlineData"].get("data"):
            return obj["inlineData"]["data"]
        jenis = str(obj.get("type", "")) + str(obj.get("mime_type", "")) + str(obj.get("mimeType", ""))
        if obj.get("data") and "audio" in jenis:
            return obj["data"]
        for v in obj.values():
            hasil = _cari_audio(v)
            if hasil:
                return hasil
    elif isinstance(obj, list):
        for v in obj:
            hasil = _cari_audio(v)
            if hasil:
                return hasil
    return None


def _minta(teks, gaya, model, voice):
    """Satu permintaan suara. Hasil: bytes audio (wav ber-header atau PCM 16-bit 24 kHz)."""
    if _cara["mode"] in (None, "interactions"):
        isi = {"type": "text", "text": teks}
        if gaya:
            isi["annotations"] = [{"type": "speech_metadata", "style": gaya}]
        body = {"model": model, "input": [{"type": "user_input", "content": [isi]}],
                "response_format": {"type": "audio", "mime_type": "audio/wav"},
                "generation_config": {"speech_config": [{"voice": voice}]}}
        try:
            data = _cari_audio(_kirim(f"{API}/interactions", body))
            if data:
                _cara["mode"] = "interactions"
                return base64.b64decode(data)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) or _cara["mode"] == "interactions":
                raise
        _cara["mode"] = "generate"
    # bentuk lama (generateContent): gaya ditulis sebagai petunjuk di depan teks
    prompt = f"Bacakan dengan gaya {gaya}:\n{teks}" if gaya else teks
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    data = _cari_audio(_kirim(f"{API}/models/{model}:generateContent", body))
    if not data:
        raise RuntimeError("Jawaban Gemini tidak berisi audio.")
    return base64.b64decode(data)


def _jeda_coba(e):
    try:
        teks = e.read().decode(errors="replace")
    except Exception:
        teks = ""
    m = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', teks)
    return (float(m.group(1)) + 1 if m else None), teks[:300]


def minta_dengan_ulang(teks, gaya, cfg):
    models = [cfg.get("model")] + [m for m in MODEL_CADANGAN if m != cfg.get("model")]
    for model in models:
        for coba in range(8):
            try:
                audio = _minta(teks, gaya, model, cfg["suara"])
                cfg["model"] = model
                return audio
            except urllib.error.HTTPError as e:
                tunggu, pesan = _jeda_coba(e)
                if e.code == 404:
                    print(f"    model {model} tidak tersedia, coba model lain", flush=True)
                    break
                if e.code in (429, 500, 503):
                    tunggu = tunggu or min(60, 5 * 2 ** coba)
                    print(f"    Gemini sibuk atau batas permintaan tercapai ({e.code}), tunggu {tunggu:.0f} detik", flush=True)
                    time.sleep(tunggu)
                    continue
                raise SystemExit(f"Gemini menolak permintaan ({e.code}): {pesan}")
            except urllib.error.URLError as e:
                print(f"    sambungan gagal ({e.reason}), coba lagi", flush=True)
                time.sleep(5)
        else:
            raise SystemExit("Gemini terus menolak setelah 8 kali coba. Kemungkinan batas harian kunci gratis sudah habis.")
    raise SystemExit("Tidak ada model suara Gemini yang tersedia untuk kunci ini.")


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def buat_suara(teks, gaya, cfg):
    """Buat (atau ambil dari simpanan) suara satu kalimat. Hasil: (wav 48 kHz mono, durasi)."""
    SUARA.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"gemini|{cfg['model']}|{cfg['suara']}|{gaya}|{teks}".encode()).hexdigest()[:16]
    wav = SUARA / f"g-{key}.wav"
    if not wav.exists():
        audio = minta_dengan_ulang(teks, gaya, dict(cfg))
        mentah = SUARA / f"g-{key}.raw"
        mentah.write_bytes(audio)
        masuk = ["-i", str(mentah)] if audio[:4] == b"RIFF" else ["-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(mentah)]
        # buang diam di awal dan akhir, sisakan sedikit supaya tidak terpotong
        potong = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08,areverse,"
                  "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12,areverse")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *masuk, "-af", potong, "-ar", str(RATE), "-ac", "1",
                        "-sample_fmt", "s16", str(wav)], check=True)
        mentah.unlink()
    return wav, ffprobe_duration(wav)


def gaya_adegan(adegan, naskah):
    dasar = naskah.get("gemini", {}).get("gaya_dasar", "")
    khusus = adegan.get("gaya_ai", "")
    return "; ".join(x for x in (dasar, khusus) if x)


def contoh(naskah, suara_list):
    """Adegan pembuka plus satu kalimat AI, dibacakan beberapa suara."""
    sys.path.insert(0, str(HERE))
    from buat_video import lafalkan
    out = HERE / "kerja" / "contoh-gemini"
    out.mkdir(parents=True, exist_ok=True)
    n = dict(naskah, mesin="gemini")
    pembuka = n["adegan"][0]
    ai = next(a for a in n["adegan"] if a["id"] == "ai-perilaku")
    kalimat = [(k.get("ucap", k["teks"]), pembuka) for k in pembuka["ketukan"]] + [(ai["ketukan"][1].get("ucap", ai["ketukan"][1]["teks"]), ai)]
    for voice in suara_list:
        cfg = dict(n["gemini"], suara=voice)
        bagian = []
        for teks, adegan in kalimat:
            wav, _ = buat_suara(lafalkan(teks, n), gaya_adegan(adegan, n), cfg)
            bagian.append(wav)
        daftar = out / "_daftar.txt"
        diam = out / "_diam.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", "0.6", "-i", f"anullsrc=r={RATE}:cl=mono",
                        "-sample_fmt", "s16", str(diam)], check=True)
        daftar.write_text("".join(f"file '{w.as_posix()}'\nfile '{diam.as_posix()}'\n" for w in bagian), encoding="utf-8")
        hasil = out / f"gemini-{voice}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(daftar), "-b:a", "160k", str(hasil)], check=True)
        print("  dibuat:", hasil, flush=True)


BAGIAN_WEB = [["pembuka", "masalah", "solusi"], ["suricata", "lab-genset", "demo-genset"],
              ["demo-petugas", "ai-perilaku", "asisten"], ["bukti", "pagar", "penutup"]]


def naskah_web(naskah, path):
    """Naskah 4 bagian untuk ditempel di situs Google AI Studio (tanpa kunci API).

    Audio hasilnya diproses seperti rekaman suara sendiri:
    python video/buat_video.py --rekaman bagian-1.wav bagian-2.wav bagian-3.wav bagian-4.wav --asal-rekaman "..."
    """
    sys.path.insert(0, str(HERE))
    from buat_video import lafalkan
    n = dict(naskah, mesin="gemini")
    per_id = {a["id"]: a for a in n["adegan"]}
    baris = [
        "# Naskah untuk Google AI Studio (suara AI Gemini)",
        "",
        "Naskah video dibagi menjadi 4 bagian. Setiap bagian dibuat suaranya sekali, lalu diunduh.",
        "",
        "## Langkah",
        "",
        "1. Buka **aistudio.google.com**, lalu pilih halaman pembuat suara (*Generate speech* / *Speech*).",
        "2. Pilih model **Gemini 3.8 Flash TTS**. Kalau model itu menolak karena batas harian, pilih model TTS lain, tapi **pakai model yang sama untuk keempat bagian**.",
        "3. Pilih mode **satu pembicara** (*single speaker*), lalu pilih suara **Charon** atau **Orus**. **Pakai suara yang sama untuk keempat bagian.**",
        "4. Untuk setiap bagian di bawah:",
        "   - Kalau ada kotak *Style instructions*, salin isi **Gaya** ke sana. Kalau tidak ada, lewati.",
        "   - Salin isi **Teks** ke kotak teks, lalu klik **Run**.",
        "   - Setelah suaranya jadi, unduh audionya. Beri nama `bagian-1`, `bagian-2`, dan seterusnya.",
        "5. Kirim keempat berkas ke chat, lalu sebutkan suara yang dipakai.",
        "",
        "Teks jangan diubah. Tanda `<short pause>` membuat jeda pendek di antara kalimat, supaya audionya bisa dipotong per kalimat. "
        "Kalau tanda itu malah ikut dibacakan, hapus semua tanda itu dan ganti dengan baris kosong.",
        "",
    ]
    nomor = 0
    for i, ids in enumerate(BAGIAN_WEB, 1):
        adegan = [per_id[x] for x in ids]
        gaya = (n["gemini"]["gaya_dasar"] + ". Scene moods in order: " +
                "; then ".join(a["gaya_ai"] for a in adegan) + ".")
        kalimat = []
        for a in adegan:
            for k in a["ketukan"]:
                nomor += 1
                kalimat.append(lafalkan(k.get("ucap", k["teks"]), n))
        baris += [f"## Bagian {i} (kalimat {nomor - len(kalimat) + 1}–{nomor})", "", "**Gaya:**", "", "```", gaya, "```", "",
                  "**Teks:**", "", "```", "\n<short pause>\n".join(kalimat), "```", ""]
    path.write_text("\n".join(baris), encoding="utf-8")
    return nomor


def teks_bagian(naskah):
    """Isi 4 bagian (gaya, teks) seperti di naskah web."""
    sys.path.insert(0, str(HERE))
    from buat_video import lafalkan
    n = dict(naskah, mesin="gemini")
    per_id = {a["id"]: a for a in n["adegan"]}
    hasil = []
    for ids in BAGIAN_WEB:
        adegan = [per_id[x] for x in ids]
        gaya = n["gemini"]["gaya_dasar"] + ". Scene moods in order: " + "; then ".join(a["gaya_ai"] for a in adegan) + "."
        kalimat = [lafalkan(k.get("ucap", k["teks"]), n) for a in adegan for k in a["ketukan"]]
        hasil.append((gaya, "\n<short pause>\n".join(kalimat)))
    return hasil


class BatasHarian(Exception):
    pass


def buat_bagian_api(naskah, voice, models):
    """Buat 4 bagian narasi lewat API: hanya 4 permintaan, cukup untuk jatah gratis harian.

    Semua bagian memakai model yang sama. Kalau satu model kena batas harian,
    keempat bagian diulang dengan model berikutnya. Hasil: (model, [wav]).
    """
    bagian = teks_bagian(naskah)
    for model in models:
        folder = HERE / "kerja" / "gemini-bagian" / f"{model}-{voice}"
        folder.mkdir(parents=True, exist_ok=True)
        wavs = []
        try:
            for i, (gaya, teks) in enumerate(bagian, 1):
                wav = folder / f"bagian-{i}.wav"
                if not wav.exists():
                    for coba in range(5):
                        try:
                            print(f"  {model}, suara {voice}: bagian {i} dari 4...", flush=True)
                            audio = _minta(teks, gaya, model, voice)
                            break
                        except urllib.error.HTTPError as e:
                            tunggu, pesan = _jeda_coba(e)
                            if e.code == 429 and "per day" in pesan:
                                raise BatasHarian(pesan)
                            if e.code == 404:
                                raise BatasHarian(f"model {model} tidak tersedia")
                            if e.code in (429, 500, 503) and coba < 4:
                                print(f"    sibuk ({e.code}), tunggu {tunggu or 20:.0f} detik", flush=True)
                                time.sleep(tunggu or 20)
                                continue
                            raise SystemExit(f"Gemini menolak permintaan ({e.code}): {pesan}")
                    mentah = folder / f"bagian-{i}.raw"
                    mentah.write_bytes(audio)
                    masuk = ["-i", str(mentah)] if audio[:4] == b"RIFF" else ["-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(mentah)]
                    subprocess.run(["ffmpeg", "-v", "error", "-y", *masuk, "-ar", str(RATE), "-ac", "1", "-sample_fmt", "s16", str(wav)], check=True)
                    mentah.unlink()
                wavs.append(wav)
            return model, wavs
        except BatasHarian as e:
            print(f"  {model} tidak bisa dipakai sekarang ({str(e)[:120]}). Coba model berikutnya.", flush=True)
    raise SystemExit("Semua model suara Gemini sedang kena batas harian untuk kunci ini.")


def main():
    naskah = json.loads((HERE / "naskah.json").read_text(encoding="utf-8"))
    if len(sys.argv) >= 2 and sys.argv[1] == "bagian":
        voice = sys.argv[2] if len(sys.argv) >= 3 else naskah["gemini"]["suara"]
        models = sys.argv[3:] or ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts"]
        model, wavs = buat_bagian_api(naskah, voice, models)
        print(f"MODEL={model}")
        for w in wavs:
            print(f"BERKAS={w}  ({ffprobe_duration(w):.1f} detik)")
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "web":
        out = Path(sys.argv[2]) if len(sys.argv) >= 3 else HERE / "naskah-ai-studio.md"
        print(f"{naskah_web(naskah, out)} kalimat ditulis ke {out}")
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "contoh":
        suara_list = sys.argv[2:] or ["Charon", "Orus", "Sadaltager", "Algenib", "Kore", "Sulafat"]
        contoh(naskah, suara_list)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
