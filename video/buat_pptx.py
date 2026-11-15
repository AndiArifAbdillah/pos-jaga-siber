"""Membuat versi PowerPoint (.pptx) dari slide presentasi (docs/slide-presentasi.html).

Setiap slide dipotret tajam (3840 x 2160) dan dipasang penuh di satu halaman
PowerPoint 16:9. Tampilannya sama persis dengan PDF; teksnya tidak bisa diedit.
Teks setiap slide ikut dimasukkan sebagai catatan pembicara dan teks alternatif,
supaya mudah dipakai saat presentasi dan tetap terbaca oleh pembaca layar.

Pemakaian (dari folder proyek):
    python video/buat_pptx.py
Hasil: ../pengumpulan/slide-pos-jaga-siber.pptx dan docs/slide-pos-jaga-siber.pptx
"""

import io
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT.parent / "pengumpulan" / "slide-pos-jaga-siber.pptx"
SALINAN = ROOT / "docs" / "slide-pos-jaga-siber.pptx"


def potret_slide():
    hasil = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        page.goto((ROOT / "docs" / "slide-presentasi.html").resolve().as_uri())
        page.wait_for_timeout(1500)
        page.evaluate("document.getElementById('counter').parentElement.style.display = 'none'")
        jumlah = page.evaluate("slides.length")
        for i in range(jumlah):
            page.evaluate(f"show({i})")
            page.wait_for_timeout(400)
            gambar = page.screenshot(type="jpeg", quality=90)
            info = page.evaluate("""i => {
                const s = slides[i];
                const judul = (s.querySelector('h1, h2') || {}).innerText || '';
                const salin = s.cloneNode(true);
                salin.querySelectorAll('.slide-num').forEach(e => e.remove());
                return {judul, teks: salin.innerText};
            }""", i)
            hasil.append((gambar, info["judul"].strip(), info["teks"]))
        browser.close()
    return hasil


def rapikan(teks):
    baris = [re.sub(r"\s+", " ", b).strip() for b in teks.splitlines()]
    return "\n".join(b for b in baris if b)


def main():
    slides = potret_slide()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)  # 13,333 x 7,5 inci (16:9)
    kosong = prs.slide_layouts[6]
    for n, (gambar, judul, teks) in enumerate(slides, 1):
        slide = prs.slides.add_slide(kosong)
        pic = slide.shapes.add_picture(io.BytesIO(gambar), 0, 0, prs.slide_width, prs.slide_height)
        pic.name = f"Slide {n}"
        pic._element.nvPicPr.cNvPr.set("descr", f"Slide {n}: {judul}" if judul else f"Slide {n}")
        slide.notes_slide.notes_text_frame.text = rapikan(teks)
    prs.core_properties.title = "Pos Jaga Siber"
    prs.core_properties.subject = "Kartika Cyber Hackathon 2026, kategori Penangkalan"
    prs.core_properties.author = "Andi Arif Abdillah, Fairuz Akhdan, Aditya Maulana Pamungkas"
    OUT.parent.mkdir(exist_ok=True)
    prs.save(OUT)
    shutil.copyfile(OUT, SALINAN)
    print(f"{len(slides)} slide -> {OUT} ({OUT.stat().st_size // 1024} KB), salinan di {SALINAN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
