"""Perintah baris: python -m pjs <perintah>

  jalan        menjalankan kotak (pembaca eve.json + dashboard)
  demo         menjalankan kotak dengan config.demo.json (tanpa Suricata)
  putar        memutar contoh catatan Suricata ke eve.json
  periksa      memeriksa rantai catatan bukti
  kode         menampilkan kode buku jaga saat ini
  cek-kode     mencocokkan kode dari buku jaga dengan catatan bukti
  uji-mikrotik mencoba sambungan API ke MikroTik
  uji-ai       mencoba meminta penjelasan ke Ollama
"""

import argparse
import logging
import shutil
import sys
import threading
from pathlib import Path

from . import config as config_mod

ROOT = Path(__file__).resolve().parent.parent
DEMO_CONFIG = ROOT / "config.demo.json"
DEMO_SAMPLE = ROOT / "lab" / "contoh_eve.jsonl"


def _load(path):
    if path is None:
        default = Path("config.json")
        path = default if default.exists() else None
    return config_mod.load(path)


def cmd_run(cfg, replay_sample=None):
    from .app import App
    from .replay import replay
    from .server import serve

    app = App(cfg)
    app.start()
    web = cfg["web"]
    httpd = serve(app, web["host"], int(web["port"]))
    shown = "localhost" if web["host"] in ("0.0.0.0", "") else web["host"]
    print(f"Pos Jaga Siber berjalan. Buka http://{shown}:{web['port']}")
    print(f"Membaca: {cfg.eve_path}")
    print(f"Blokir: {app.responder.mode} | AI: {app.explainer.state} | Tanda tangan: {app.evidence.signer.backend}")
    stop = threading.Event()
    if replay_sample:
        def play():
            replay(replay_sample, cfg.eve_path, out=lambda s: None, stop_event=stop)
            print("Contoh skenario selesai diputar.")
        threading.Thread(target=play, name="pemutar-contoh", daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMematikan kotak...")
    finally:
        stop.set()
        httpd.server_close()
        app.stop()


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(prog="python -m pjs", description="Pos Jaga Siber")
    parser.add_argument("--config", help="berkas konfigurasi (bawaan: config.json kalau ada)")
    parser.add_argument("-v", "--verbose", action="store_true", help="tampilkan catatan rinci")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("jalan", help="menjalankan kotak")

    p_demo = sub.add_parser("demo", help="menjalankan kotak dengan konfigurasi demo")
    p_demo.add_argument("--putar", action="store_true", help="sekalian memutar contoh skenario otomatis")
    p_demo.add_argument("--baru", action="store_true", help="hapus data demo lama dan mulai dari nol")
    p_demo.add_argument("--port", type=int, help="ganti port dashboard")
    p_demo.add_argument("--model", help="nama model Ollama yang dipakai, misalnya qwen3.5-4b:latest")

    p_play = sub.add_parser("putar", help="memutar contoh catatan Suricata")
    p_play.add_argument("berkas", nargs="?", default=str(DEMO_SAMPLE))
    p_play.add_argument("--ke", help="berkas eve.json tujuan (bawaan: eve_path dari konfigurasi)")
    p_play.add_argument("--jeda", type=float, default=0.3, help="jeda antar catatan (detik)")
    p_play.add_argument("--langkah", action="store_true", help="tunggu Enter sebelum setiap skenario")

    sub.add_parser("periksa", help="memeriksa rantai catatan bukti")
    sub.add_parser("kode", help="menampilkan kode buku jaga")
    p_code = sub.add_parser("cek-kode", help="mencocokkan kode buku jaga")
    p_code.add_argument("kode")
    sub.add_parser("uji-mikrotik", help="mencoba sambungan ke MikroTik")
    p_ai = sub.add_parser("uji-ai", help="mencoba penjelas AI")
    p_ai.add_argument("--model", help="nama model Ollama yang dicoba")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(name)s: %(message)s")

    if args.command == "demo":
        cfg = config_mod.load(args.config or DEMO_CONFIG)
        if args.port:
            cfg.raw["web"]["port"] = args.port
        if args.model:
            cfg.raw["ollama"]["model"] = args.model
        if args.baru and cfg.data_dir.exists():
            if cfg.data_dir.name != "data-demo":
                parser.error("--baru hanya boleh menghapus folder data-demo.")
            shutil.rmtree(cfg.data_dir)
            print(f"Data demo lama dihapus: {cfg.data_dir}")
        return cmd_run(cfg, replay_sample=DEMO_SAMPLE if args.putar else None)

    cfg = _load(args.config)

    if args.command == "jalan":
        return cmd_run(cfg)

    if args.command == "putar":
        from .replay import replay

        target = Path(args.ke) if args.ke else cfg.eve_path
        print(f"Memutar {args.berkas} ke {target}")
        count = replay(args.berkas, target, delay_s=args.jeda, step=args.langkah)
        print(f"Selesai: {count} catatan ditulis.")
        return 0

    from .evidence import EvidenceLog

    evidence_path = cfg.data_dir / "bukti.jsonl"
    if args.command in ("periksa", "kode", "cek-kode"):
        if not evidence_path.exists():
            print(f"Belum ada catatan bukti di {evidence_path}")
            return 1
        log_ = EvidenceLog(evidence_path, cfg.data_dir / "kunci_kotak.key")
        if args.command == "periksa":
            result = log_.verify()
            print(("UTUH  " if result["ok"] else "PUTUS ") + result["message"])
            return 0 if result["ok"] else 1
        if args.command == "kode":
            print(f"Kode buku jaga: {log_.code()}  (entri #{log_.count})")
            return 0
        seq = log_.find_code(args.kode)
        if seq is None:
            print(f"Kode {args.kode} TIDAK ditemukan. Catatan mungkin sudah dipotong atau ditulis ulang.")
            return 1
        print(f"Kode {args.kode} cocok dengan entri #{seq}. Catatan sampai titik itu masih asli.")
        return 0

    if args.command == "uji-mikrotik":
        from .responder import MikroTikResponder

        responder = MikroTikResponder(cfg["mikrotik"])
        if not responder.enabled:
            print("MikroTik belum diaktifkan di konfigurasi (mikrotik.enabled = false).")
            return 1
        name, entries = responder.check()
        print(f"Tersambung ke router '{name}'. Isi daftar {responder.list_name}: {len(entries)} alamat.")
        for row in entries:
            print(f"  {row.get('address')}  sisa {row.get('timeout', '-')}  {row.get('comment', '')}")
        return 0

    if args.command == "uji-ai":
        import time

        from .explainer import STYLE, Explainer

        model = args.model or cfg["ollama"]["model"]
        explainer = Explainer({**cfg["ollama"], "enabled": True, "model": model}, on_ready=None, on_failed=None)
        models = explainer.list_models()
        if models is None:
            print(f"Ollama tidak bisa dihubungi di {explainer.url}")
            return 1
        if not explainer.has_model(models):
            print(f"Model {model} belum diunduh. Model yang ada: {', '.join(models) or '(belum ada)'}")
            print(f"Unduh dengan: ollama pull {model}   atau pakai --model <nama model yang ada>")
            return 1
        prompt = (
            f'Jawab hanya dengan JSON {{"apa": "...", "kenapa": "..."}}. {STYLE} '
            "Kejadian: laptop tak dikenal mengirim perintah mematikan genset markas."
        )
        print(f"Bertanya ke model {explainer.model} (permintaan pertama bisa lama karena model sedang dimuat)...")
        started = time.time()
        result = explainer.ask(prompt)
        print(f"Selesai dalam {time.time() - started:.0f} detik.")
        print("Apa    :", result["what"])
        print("Kenapa :", result["why"])
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
