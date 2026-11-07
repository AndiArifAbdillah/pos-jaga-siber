"""Merekam gambar dashboard ASLI untuk video.

Skrip ini menjalankan kotak dalam mode demo di port tersendiri, memutar contoh
catatan sensor bab demi bab, lalu memotret dashboard (resolusi 2x) di setiap
keadaan penting. Hasilnya dipakai buat_video.py.

Hasil di folder video/bahan/:
  *.png          tangkapan layar halaman penuh (lebar 1600 px, kerapatan 2x)
  kotak.json     posisi elemen penting di setiap tangkapan (untuk gerakan kamera)
  serangan.txt   keluaran asli skrip serangan ke genset tiruan
  status.json    data dashboard terakhir (kode buku jaga, dll.)

Contoh:
  python video/rekam_dashboard.py --model qwen3.5-4b:latest
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "bahan"
WORK = HERE / "kerja"
sys.path.insert(0, str(ROOT))

from pjs.replay import replay  # noqa: E402

PORT = 8095
GENSET_PORT, GENSET_WEB = 5022, 8096
VIEW = {"width": 1600, "height": 900}

# Elemen yang posisinya dicatat untuk kamera dan sorotan.
BOXES = {
    "semua": "body",
    "atas": ".top",
    "kotak-ringkas": ".tiles",
    "kotak-perlu": "#tile-need",
    "kotak-isolasi": ".tiles .tile:nth-child(2)",
    "kotak-bukti": "#tile-ev",
    "daftar": ".list-panel",
    "rincian": "#detail",
    "rincian-atas": "#detail .d-head",
    "rute": "#detail .route",
    "ml": "#detail .ml",
    "penjelasan": "#detail .ai-card",
    "langkah": "#detail .steps",
    "tombol": "#detail .actions",
    "asisten": ".assistant",
    "tanya": "#ask-form",
    "jawaban": "#ask-answer",
    "laporan": "#report-text",
    "bukti": ".side .panel:last-child",
    "kode": ".code-box",
    "banner": "#banner",
    "perangkat-ot": ".side .panel:first-child",
}


def api(path, body=None):
    url = f"http://127.0.0.1:{PORT}{path}"
    if body is None:
        with urllib.request.urlopen(url, timeout=120) as r:
            return json.loads(r.read())
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "X-PJS": "1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def chapters():
    """Bagi contoh_eve.jsonl menjadi bab: [(judul, [baris])]."""
    result = []
    for line in (ROOT / "lab" / "contoh_eve.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if "_bab" in event:
            result.append((event["_bab"], []))
        elif result:
            result[-1][1].append(line)
    return [c for c in result if c[1]]


def play(lines, eve):
    tmp = WORK / "bab.jsonl"
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    replay(tmp, eve, delay_s=0.25, chapter_pause_s=0, out=lambda s: None)


def wait_quiet(min_incidents, extra_s=0.0, timeout=180):
    """Tunggu sampai jumlah kejadian cukup dan semua penjelasan AI selesai."""
    time.sleep(extra_s)
    end = time.time() + timeout
    while time.time() < end:
        s = api("/api/status")
        if len(s["incidents"]) >= min_incidents and not any((i["explanation"] or {}).get("pending") for i in s["incidents"]):
            return s
        time.sleep(1)
    raise SystemExit("Menunggu dashboard terlalu lama.")


def incident_id(status, kind):
    return next(i["id"] for i in status["incidents"] if i["kind"] == kind)


def main():
    parser = argparse.ArgumentParser(description="Rekam gambar dashboard asli untuk video")
    parser.add_argument("--model", help="model Ollama (bawaan: dari config.demo.json)")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / "config.demo.json").read_text(encoding="utf-8"))
    cfg.update(data_dir="data-demo", eve_path="data-demo/eve.json", operator="Serda Contoh")
    cfg["web"] = {"host": "127.0.0.1", "port": PORT}
    cfg["anomaly"]["seed_file"] = str(ROOT / "lab" / "contoh_riwayat_normal.jsonl")
    if args.model:
        cfg["ollama"]["model"] = args.model
    cfg_path = WORK / "config.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    eve = WORK / "data-demo" / "eve.json"

    box = subprocess.Popen([sys.executable, "-m", "pjs", "--config", str(cfg_path), "demo", "--baru"], cwd=ROOT)
    genset = subprocess.Popen([sys.executable, str(ROOT / "lab" / "genset_tiruan.py"), "--host", "127.0.0.1",
                               "--port", str(GENSET_PORT), "--web-port", str(GENSET_WEB)], cwd=ROOT)
    boxes = {}
    try:
        for _ in range(120):
            try:
                if api("/api/status")["links"]["ai"] not in ("memeriksa", "memuat"):
                    break
            except OSError:
                pass
            time.sleep(1)
        print("Kotak siap:", api("/api/status")["links"]["ai"])

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport=VIEW, device_scale_factor=2)

            def shot(name):
                page.wait_for_timeout(900)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
                found = {}
                for key, selector in BOXES.items():
                    rect = page.evaluate(
                        "s => { const e = document.querySelector(s); if (!e || !e.offsetParent && s !== 'body') return null;"
                        " const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.width, r.height]; }",
                        selector,
                    )
                    if rect and rect[2] > 0:
                        found[key] = [round(v, 1) for v in rect]
                found["ukuran"] = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
                boxes[name] = found
                print("  gambar:", name)

            def select(iid):
                page.evaluate("id => document.querySelector(`.inc[data-id='${id}']`).click()", iid)
                page.wait_for_timeout(500)

            # Genset tiruan: lampu menyala, serangan, lampu mati (lab, bukan dashboard).
            page.goto(f"http://127.0.0.1:{GENSET_WEB}/")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "lampu-nyala.png"))
            attack = subprocess.run([sys.executable, str(ROOT / "lab" / "serangan_genset.py"), "--target", "127.0.0.1",
                                     "--port", str(GENSET_PORT)], cwd=ROOT, capture_output=True, text=True)
            (OUT / "serangan.txt").write_text(attack.stdout.strip() + "\n", encoding="utf-8")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "lampu-mati.png"))
            print("  gambar: lampu-nyala, lampu-mati")

            page.goto(f"http://127.0.0.1:{PORT}/")
            parts = chapters()
            play(parts[0][1], eve)                       # pemanasan
            wait_quiet(0, extra_s=3)
            shot("tenang")

            play(parts[1][1], eve)                       # skenario 1: genset
            s = wait_quiet(2)
            genset_id = incident_id(s, "ot_tulis")
            select(genset_id)
            shot("genset")
            page.evaluate("document.querySelector('#detail input[data-step=\"0\"]').click()")
            page.wait_for_timeout(1500)
            shot("genset-centang")

            play(parts[2][1], eve)                       # skenario 2: kamera
            s = wait_quiet(3, extra_s=13)                # tunggu AI perilaku menilai rentang 10 detik
            select(incident_id(s, "ot_ke_luar"))
            shot("kamera")

            play(parts[3][1], eve)                       # skenario 3: sinyal berkala
            s = wait_quiet(4)
            select(incident_id(s, "sinyal_berkala"))
            shot("beacon")

            # Skenario 5: mulai tepat setelah awal rentang 10 detik, supaya ke-14 sambungan
            # pemindaian masuk satu rentang yang sama (seperti yang disebut di narasi).
            time.sleep((10 - time.time() % 10) + 0.3)
            play(parts[4][1], eve)                       # skenario 5: AI perilaku
            s = wait_quiet(5, extra_s=14)
            select(incident_id(s, "perilaku_aneh"))
            shot("pintu")

            select(genset_id)
            page.fill("#ask-input", "Apa yang terjadi pada genset hari ini?")
            shot("asisten-tanya")
            page.click("#ask-btn")
            page.wait_for_function("document.querySelector('#ask-answer .src') !== null", timeout=120000)
            shot("asisten-jawab")
            page.fill("#ask-input", "Berapa suhu ruang server sekarang?")
            page.click("#ask-btn")
            page.wait_for_function("document.querySelector('#ask-answer').innerText.includes('Dijawab') || document.querySelector('#ask-answer').innerText.includes('cocok')", timeout=120000)
            page.wait_for_timeout(1500)
            shot("asisten-tidak-tahu")
            page.click("#btn-report")
            page.wait_for_function("!document.querySelector('#report-text').hidden", timeout=120000)
            page.wait_for_timeout(3800)                  # tunggu pesan pop-up hilang
            shot("laporan")

            subprocess.run([sys.executable, str(ROOT / "lab" / "ubah_catatan.py"), str(WORK / "data-demo" / "bukti.jsonl")],
                           cwd=ROOT, check=True)
            page.click("#btn-check")
            page.wait_for_timeout(2000)
            shot("putus")
            browser.close()

        (OUT / "kotak.json").write_text(json.dumps(boxes, indent=1), encoding="utf-8")
        (OUT / "status.json").write_text(json.dumps(api("/api/status"), ensure_ascii=False, indent=1), encoding="utf-8")
        print("Selesai. Hasil di", OUT)
    finally:
        box.terminate()
        genset.terminate()


if __name__ == "__main__":
    main()
