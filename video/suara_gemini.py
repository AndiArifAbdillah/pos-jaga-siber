"""Narasi dengan suara AI Google Gemini (yang dipakai di Google AI Studio).

Butuh kunci API dari Google AI Studio (aistudio.google.com, menu "Get API key").
Simpan kunci di variabel lingkungan GEMINI_API_KEY. Di Windows, jalankan sekali
di PowerShell (ganti KUNCI dengan kunci milikmu):

    [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "KUNCI", "User")

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


def kunci():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k and sys.platform == "win32":
        # variabel yang baru disetel lewat PowerShell belum terlihat oleh proses yang sudah berjalan
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                k = winreg.QueryValueEx(reg, "GEMINI_API_KEY")[0]
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


def main():
    naskah = json.loads((HERE / "naskah.json").read_text(encoding="utf-8"))
    if len(sys.argv) >= 2 and sys.argv[1] == "contoh":
        suara_list = sys.argv[2:] or ["Charon", "Orus", "Sadaltager", "Algenib", "Kore", "Sulafat"]
        contoh(naskah, suara_list)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
