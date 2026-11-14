"""Menyiapkan berkas pengumpulan karya: slide PDF, 5 screenshot, thumbnail, teks YouTube.

Hasil di folder pengumpulan/ (di samping folder proyek):
  slide-pos-jaga-siber.pdf   slide 15 halaman dari docs/slide-presentasi.html
  screenshot-1..5.jpg        1920x1080, dari gambar dashboard asli (video/bahan)
  thumbnail.jpg              1200x630, di bawah 500 KB
  youtube.txt                judul, deskripsi dengan bab waktu, dan tag

Butuh: video/bahan (dari rekam_dashboard.py), video/kerja/waktu.json (dari buat_video.py).

  python video/buat_pengumpulan.py
"""

import base64
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BAHAN = HERE / "bahan"
OUT = ROOT.parent / "pengumpulan"

# (nama berkas, gambar asli, kotak yang harus terlihat)
SCREENSHOTS = [
    ("screenshot-1-serangan-genset.jpg", "genset", "rincian-atas"),
    ("screenshot-2-ai-deteksi-perilaku.jpg", "pintu", "ml"),
    ("screenshot-3-petugas-memutuskan.jpg", "kamera", "ml"),
    ("screenshot-4-asisten-piket.jpg", "asisten-jawab", "asisten"),
    ("screenshot-5-catatan-bukti.jpg", "putus", "banner"),
]

THUMB = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;width:1200px;height:630px;overflow:hidden;background:#0b0f0a;font-family:"Segoe UI",sans-serif;color:#eef1e8}
.bg{position:absolute;inset:0;background:radial-gradient(700px 420px at 20% 30%,rgba(188,204,134,.16),transparent 65%),
 linear-gradient(rgba(188,204,134,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(188,204,134,.05) 1px,transparent 1px);background-size:auto,48px 48px,48px 48px}
.kiri{position:absolute;left:60px;top:64px;width:600px}
.kiri svg{width:76px;height:76px;color:#bccc86}
h1{margin:14px 0 0;font:700 62px/1 Bahnschrift,sans-serif;letter-spacing:.04em;white-space:nowrap}
p{margin:18px 0 0;width:540px;font:600 26px/1.3 Bahnschrift,sans-serif;color:#d9dfcf}
.cip{display:inline-block;margin:22px 8px 0 0;font:700 16px Bahnschrift;letter-spacing:.05em;padding:7px 12px;border-radius:8px}
.a{background:#bccc86;color:#1a2010}.b{border:1px solid #ff8f84;color:#ff8f84}.c{border:1px solid #9cc3f5;color:#9cc3f5}
.kaki{position:absolute;left:64px;bottom:40px;font:600 19px Bahnschrift;letter-spacing:.12em;color:#a3ac97;text-transform:uppercase}
.layar{position:absolute;left:640px;top:120px;width:620px;height:349px;border-radius:14px;overflow:hidden;border:1px solid #3d4936;
 box-shadow:0 30px 70px rgba(0,0,0,.7),0 0 60px rgba(188,204,134,.12);transform:perspective(1400px) rotateY(-14deg) rotateX(4deg);transform-origin:left center}
.layar img{width:100%;display:block}
</style></head><body><div class="bg"></div>
<div class="kiri">
 <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M32 5l23 8v17c0 14-10 24-23 29C19 54 9 44 9 30V13z"/><path d="M22 31l7 7 13-14"/></svg>
 <h1>POS JAGA SIBER</h1>
 <p>Penjaga jaringan IT/OT markas berbasis AI. Bekerja mandiri, menjelaskan dengan bahasa sehari-hari.</p>
 <span class="cip a">3 PERAN AI LOKAL</span><span class="cip b">ISOLASI OTOMATIS</span><span class="cip c">BUKTI ANTI-UBAH</span>
</div>
<div class="kaki">Kartika Cyber Hackathon 2026 · Kategori Penangkalan</div>
<div class="layar"><img src="SUMBER"></div>
</body></html>"""


def crop_shot(name, src, key, kotak):
    """Potong bagian 1600x900 (ukuran layar) yang memuat kotak penting, lalu jadikan 1920x1080."""
    img = Image.open(BAHAN / f"{src}.png")
    width_css, height_css = kotak[src]["ukuran"]
    x, y, w, h = kotak[src][key]
    top = max(0, min(height_css - 900, y + h / 2 - 450))
    scale = img.width / width_css
    box = (0, int(top * scale), img.width, int((top + 900) * scale))
    img.crop(box).resize((1920, 1080), Image.LANCZOS).convert("RGB").save(OUT / name, quality=90)


def chapters():
    waktu = json.loads((HERE / "kerja" / "waktu.json").read_text(encoding="utf-8"))
    names = {"pembuka": "Pembuka"}
    lines = []
    for s in waktu:
        title = names.get(s["id"]) or s["bab"].split("·", 1)[-1].strip()
        t = int(s["offset"])
        lines.append(f"{t // 60}:{t % 60:02d} {title[:1].upper() + title[1:]}")
    return "\n".join(lines)


def kredit_narasi():
    info_path = HERE / "kerja" / "narasi-info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {"sumber": "buatan", "suara": "id-ID-ArdiNeural"}
    if info["sumber"] == "rekaman":
        return f"Narasi dibacakan oleh {info.get('pembaca') or 'anggota tim'}."
    if info["sumber"] == "gemini":
        return f"Narasi memakai suara AI Google Gemini ({info['model']}, suara {info['suara']})."
    return f"Narasi memakai suara sintetis Microsoft ({info['suara']})."


def main():
    OUT.mkdir(exist_ok=True)
    kotak = json.loads((BAHAN / "kotak.json").read_text(encoding="utf-8"))
    for name, src, key in SCREENSHOTS:
        crop_shot(name, src, key, kotak)
        print("  ", name)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto((ROOT / "docs" / "slide-presentasi.html").resolve().as_uri())
        page.wait_for_timeout(1200)
        page.evaluate("document.getElementById('counter').parentElement.style.display = 'none'")
        pages = []
        for i in range(page.evaluate("slides.length")):
            page.evaluate(f"show({i})")
            page.wait_for_timeout(400)
            tmp = OUT / f"_slide{i:02d}.png"
            page.screenshot(path=str(tmp))
            pages.append(Image.open(tmp).convert("RGB"))
        pdf = OUT / "slide-pos-jaga-siber.pdf"
        pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=96)
        for f in OUT.glob("_slide*.png"):
            f.unlink()
        print("   slide-pos-jaga-siber.pdf:", len(pages), "halaman")

        thumb_src = OUT / "screenshot-1-serangan-genset.jpg"
        data_uri = "data:image/jpeg;base64," + base64.b64encode(thumb_src.read_bytes()).decode()
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.set_content(THUMB.replace("SUMBER", data_uri))
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "thumbnail.jpg"), type="jpeg", quality=88)
        browser.close()
    size = (OUT / "thumbnail.jpg").stat().st_size // 1024
    print(f"   thumbnail.jpg: 1200x630, {size} KB")

    (OUT / "youtube.txt").write_text(f"""JUDUL
Pos Jaga Siber: Penjaga Jaringan IT/OT Markas Berbasis AI | Kartika Cyber Hackathon 2026

DESKRIPSI
Pos Jaga Siber adalah kotak penjaga jaringan berbasis AI untuk markas satuan. Kotak ini mengawasi komputer kantor (IT) dan peralatan penting (OT) seperti genset, kamera CCTV, dan kunci pintu; langsung mengisolasi ancaman kritis lewat router MikroTik; menjelaskan setiap kejadian dalam bahasa sehari-hari dengan AI lokal; dan mencatat semuanya di catatan bukti anti-ubah. Kotak bekerja mandiri: tetap menjaga meskipun internet putus, dan data markas tidak keluar.

Kategori Penangkalan · Kartika Cyber Hackathon 2026
Tim: Andi Arif Abdillah, Fairuz Akhdan, Aditya Maulana Pamungkas
Kode dan dokumentasi: https://github.com/AndiArifAbdillah/pos-jaga-siber

Bab:
{chapters()}

Catatan: rekaman dashboard memakai contoh catatan sensor (mode demo) dan blokir mode uji. Serangan ke genset tiruan dijalankan sungguhan di lab tim.

Komponen pihak ketiga: Suricata (OISF), aturan ET Open, MikroTik RouterOS/CHR, Ollama, model Qwen, Python, VirtualBox. Kode, dokumentasi, dan video dikembangkan dengan bantuan asisten AI (Claude, buatan Anthropic). {kredit_narasi()}

TAG
keamanan siber, IDS, OT security, Modbus, Suricata, MikroTik, machine learning, Isolation Forest, AI lokal, Ollama, Kartika Cyber Hackathon 2026, TNI AD
""", encoding="utf-8")
    print("   youtube.txt")
    print("Selesai:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
