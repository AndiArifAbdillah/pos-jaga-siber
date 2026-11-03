"""Server web kotak: menyajikan dashboard operator dan API JSON.

Hanya memakai pustaka bawaan Python, tanpa memuat apa pun dari internet.

API:
  GET  /api/status                      semua data untuk dashboard
  POST /api/insiden/<id>/isolasi        isolasi perangkat asal
  POST /api/insiden/<id>/lepas          batalkan isolasi
  POST /api/insiden/<id>/bukan-ancaman  tandai bukan ancaman
  POST /api/insiden/<id>/buka-lagi      buka lagi kejadian
  POST /api/insiden/<id>/langkah        {"index": 0, "checked": true}
  POST /api/bukti/periksa               periksa rantai catatan bukti
  POST /api/asisten/tanya               {"pertanyaan": "..."} tanya kotak
  POST /api/asisten/laporan-piket       {"jam": 8} laporan ganti piket
  GET  /laporan/<id>                    laporan siap cetak

Setiap POST wajib membawa kepala "X-PJS: 1". Halaman web lain tidak bisa
menambahkan kepala ini tanpa izin, jadi situs asing tidak bisa menekan tombol
dashboard diam-diam (perlindungan CSRF sederhana).
"""

import html
import json
import logging
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

log = logging.getLogger("pjs.server")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
STATIC_TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".svg": "image/svg+xml"}
ACTION_PATH = re.compile(r"^/api/insiden/(PJS-\d{4,})/(isolasi|lepas|bukan-ancaman|buka-lagi|langkah)$")
REPORT_PATH = re.compile(r"^/laporan/(PJS-\d{4,})$")
SEVERITY_LABEL = {"kritis": "Kritis", "tinggi": "Tinggi", "sedang": "Sedang", "rendah": "Rendah"}
STATUS_LABEL = {"menunggu": "Menunggu keputusan", "diisolasi": "Diisolasi", "dilepas": "Isolasi dilepas", "bukan_ancaman": "Bukan ancaman"}


def _fmt(ts):
    return datetime.fromtimestamp(ts).strftime("%d-%m-%Y %H:%M:%S") if ts else "-"


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PosJagaSiber"

        def log_message(self, fmt, *args):
            log.debug("%s - %s", self.address_string(), fmt % args)

        # --- kirim balasan ------------------------------------------------
        def _send(self, code, body, content_type):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False), "application/json")

        # --- GET ----------------------------------------------------------
        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path == "/api/status":
                return self._json(200, app.status())
            match = REPORT_PATH.match(path)
            if match:
                query = parse_qs(urlparse(self.path).query)
                operator = (query.get("operator") or [app.cfg["operator"]])[0][:60]
                return self._report(match.group(1), operator)
            if path == "/":
                path = "/index.html"
            return self._static(path)

        def _static(self, path):
            target = (WEB_DIR / path.lstrip("/")).resolve()
            if WEB_DIR not in target.parents or not target.is_file() or target.suffix not in STATIC_TYPES:
                return self._send(404, "Tidak ditemukan", "text/plain")
            self._send(200, target.read_bytes(), STATIC_TYPES[target.suffix])

        # --- POST ---------------------------------------------------------
        def do_POST(self):
            if self.headers.get("X-PJS") != "1":
                return self._json(403, {"ok": False, "message": "Permintaan ditolak."})
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            except ValueError:
                return self._json(400, {"ok": False, "message": "Isi permintaan tidak bisa dibaca."})
            operator = str(body.get("operator") or app.cfg["operator"])[:60]
            path = urlparse(self.path).path
            if path == "/api/bukti/periksa":
                result = app.check_integrity(record=True, operator=operator)
                return self._json(200, {"ok": True, "integrity": result})
            if path == "/api/asisten/tanya":
                result = app.assistant.ask(body.get("pertanyaan", ""), operator=operator)
                return self._json(200 if result["ok"] else 400, result)
            if path == "/api/asisten/laporan-piket":
                try:
                    hours = int(body.get("jam", 8))
                except (TypeError, ValueError):
                    hours = 8
                return self._json(200, app.assistant.shift_report(hours, operator=operator))
            match = ACTION_PATH.match(path)
            if not match:
                return self._json(404, {"ok": False, "message": "Alamat tidak dikenal."})
            incident_id, action = match.groups()
            d = app.detector
            if action == "isolasi":
                ok, message = d.isolate(incident_id, by="operator", operator=operator)
            elif action == "lepas":
                ok, message = d.release(incident_id, operator=operator)
            elif action == "bukan-ancaman":
                ok, message = d.dismiss(incident_id, operator=operator)
            elif action == "buka-lagi":
                ok, message = d.reopen(incident_id, operator=operator)
            else:
                try:
                    index = int(body.get("index"))
                except (TypeError, ValueError):
                    return self._json(400, {"ok": False, "message": "Nomor langkah tidak sah."})
                ok, message = d.set_step(incident_id, index, bool(body.get("checked")), operator=operator)
            self._json(200 if ok else 409, {"ok": ok, "message": message})

        # --- laporan siap cetak -------------------------------------------
        def _report(self, incident_id, operator):
            inc = app.store.get_incident(incident_id)
            if not inc:
                return self._send(404, "Kejadian tidak ditemukan", "text/plain")
            app.detector.mark_reported(incident_id, operator=operator)
            view = app.incident_view(app.store.get_incident(incident_id), app.store.isolated_ips())
            e = html.escape
            steps = "".join(
                f"<li>{'[x]' if s['checked'] else '[ ]'} {e(s['text'])}</li>" for s in view["steps"]
            )
            timeline = "".join(
                f"<tr><td>#{x['seq']}</td><td>{e(x['time'])}</td><td>{e(x['text'])}</td></tr>"
                for x in app.report_entries(incident_id)
            )
            exp = view["explanation"] or {}
            source = f"AI lokal ({e(exp.get('model') or '')})" if exp.get("source") == "ai" else "penjelasan bawaan"
            page = f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Laporan {e(incident_id)}</title>
<style>
body{{font:14px/1.5 system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#111}}
h1{{font-size:20px;margin:0}} h2{{font-size:15px;margin:20px 0 6px;border-bottom:1px solid #999}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top}}
.muted{{color:#555}} .sign{{display:flex;justify-content:space-between;margin-top:48px}}
@media print{{button{{display:none}}}}
</style></head><body>
<button onclick="window.print()">Cetak</button>
<p class="muted">{e(app.cfg['box_name'])} &middot; {e(app.cfg['unit'])}</p>
<h1>Laporan kejadian {e(incident_id)}</h1>
<p><b>{e(view['title'])}</b></p>
<table>
<tr><th>Tingkat</th><td>{e(SEVERITY_LABEL.get(view['severity'], view['severity']))}</td></tr>
<tr><th>Status</th><td>{e(STATUS_LABEL.get(view['status'], view['status']))}</td></tr>
<tr><th>Dari</th><td>{e(view['src']['name'] or '-')} ({e(view['src']['ip'] or '-')})</td></tr>
<tr><th>Ke</th><td>{e(view['dst']['name'] or '-')} ({e(view['dst']['ip'] or '-')})</td></tr>
<tr><th>Pertama terlihat</th><td>{_fmt(view['first_seen'])}</td></tr>
<tr><th>Terakhir terlihat</th><td>{_fmt(view['last_seen'])}</td></tr>
<tr><th>Jumlah</th><td>{view['count']} kali</td></tr>
</table>
<h2>Penjelasan ({source})</h2>
<p><b>Apa yang terjadi.</b> {e(exp.get('what', '-'))}</p>
<p><b>Kenapa berbahaya.</b> {e(exp.get('why', '-'))}</p>
<h2>Langkah SOP</h2><ul style="list-style:none;padding-left:0">{steps}</ul>
<h2>Jejak di catatan bukti</h2>
<table><tr><th>No.</th><th>Waktu</th><th>Catatan</th></tr>{timeline}</table>
<p class="muted">Kode buku jaga saat laporan dibuat: <b>{e(app.evidence.code())}</b>.
Kode ini bisa dicocokkan dengan perintah <code>python -m pjs cek-kode</code>.</p>
<div class="sign"><div>Petugas jaga<br><br><br>( ........................ )</div>
<div>Mengetahui<br><br><br>( ........................ )</div></div>
</body></html>"""
            self._send(200, page, "text/html")

    return Handler


def serve(app, host, port):
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    httpd.daemon_threads = True
    return httpd
