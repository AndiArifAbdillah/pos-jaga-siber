"""Merakit semua bagian kotak dan menyusun data untuk dashboard."""

import logging
import threading
import time
from datetime import datetime

from . import __version__
from .assistant import ShiftAssistant
from .collector import EveTailer
from .detector import Detector
from .evidence import EvidenceLog
from .explainer import Explainer
from .responder import MikroTikResponder
from .store import Store

log = logging.getLogger("pjs.app")

ENTRY_TEXT = {
    "kotak_menyala": "Kotak dinyalakan",
    "kotak_dimatikan": "Kotak dimatikan",
    "kejadian_baru": "{incident} dicatat: {title}",
    "isolasi_otomatis": "{incident}: {ip} diisolasi otomatis",
    "isolasi_operator": "{incident}: {ip} diisolasi oleh {operator}",
    "isolasi_gagal": "{incident}: isolasi {ip} gagal",
    "isolasi_dilepas": "{incident}: isolasi {ip} dilepas oleh {operator}",
    "bukan_ancaman": "{incident}: ditandai bukan ancaman oleh {operator}",
    "dibuka_lagi": "{incident}: dibuka lagi oleh {operator}",
    "langkah_dicentang": "{incident}: langkah {step} selesai ({operator})",
    "langkah_dibatalkan": "{incident}: centang langkah {step} dibatalkan ({operator})",
    "laporan_dibuat": "{incident}: laporan dibuat oleh {operator}",
    "penjelasan_ai": "{incident}: penjelasan AI tersusun",
    "pemeriksaan_rantai": "Rantai diperiksa: {result}",
    "tanya_kotak": "Asisten ditanya oleh {operator}",
    "laporan_piket": "Laporan ganti piket {hours} jam dibuat oleh {operator}",
}


def describe(entry):
    data = {k: ("-" if v is None else v) for k, v in (entry.get("data") or {}).items()}
    template = ENTRY_TEXT.get(entry.get("kind"), entry.get("kind", "?"))
    try:
        return template.format(**data)
    except (KeyError, IndexError):
        return entry.get("kind", "?")


def iso(ts):
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds") if ts else None


class App:
    def __init__(self, cfg):
        self.cfg = cfg
        cfg.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = Store(cfg.data_dir / "pjs.sqlite3")
        self.evidence = EvidenceLog(cfg.data_dir / "bukti.jsonl", cfg.data_dir / "kunci_kotak.key")
        self.responder = MikroTikResponder(cfg["mikrotik"])
        self.explainer = Explainer(
            cfg["ollama"],
            on_ready=lambda i, e: self.detector.apply_explanation(i, e),
            on_failed=lambda i, r: self.detector.explanation_failed(i, r),
        )
        self.detector = Detector(cfg, self.store, self.evidence, self.responder, self.explainer)
        self.tailer = EveTailer(cfg.eve_path, self.detector.process, from_start=cfg["read_from_start"])
        self.assistant = ShiftAssistant(self)
        self._integrity = self.evidence.verify()
        self._integrity_lock = threading.Lock()

    def start(self):
        self.explainer.start()
        self.evidence.append("kotak_menyala", {
            "version": __version__, "blokir": self.responder.mode,
            "ai": self.explainer.state, "signer": self.evidence.signer.backend,
            "ai_perilaku": self.detector.watcher.status(self.detector.learning_active())["state"],
        })
        self.check_integrity(record=False)
        self.tailer.start()
        threading.Thread(target=self._integrity_loop, name="pemeriksa-rantai", daemon=True).start()
        threading.Thread(target=self._behavior_loop, name="penilai-perilaku", daemon=True).start()

    def _behavior_loop(self):
        while True:
            time.sleep(1)
            try:
                self.detector.flush_behavior()
            except Exception:
                log.exception("Penilaian perilaku gagal, dicoba lagi.")

    def stop(self):
        self.tailer.stop()
        self.evidence.append("kotak_dimatikan", {})

    def _integrity_loop(self):
        while True:
            time.sleep(60)
            self.check_integrity(record=False)

    def check_integrity(self, record=True, operator=None):
        result = self.evidence.verify()
        with self._integrity_lock:
            self._integrity = result
        if record:
            self.evidence.append("pemeriksaan_rantai", {
                "result": "utuh" if result["ok"] else f"putus di #{result['broken_at']}", "operator": operator,
            })
        return result

    # --- data untuk dashboard -------------------------------------------
    def _party(self, ip, isolated):
        device = self.store.get_device(ip) if ip else None
        return {
            "ip": ip or None,
            "name": self.detector.device_name(ip) if ip else None,
            "zone": self.cfg.zone_of(ip) if ip else None,
            "kind": (device or {}).get("kind"),
            "isolated": ip in isolated,
        }

    def incident_view(self, inc, isolated):
        return {
            "id": inc["id"], "kind": inc["kind"], "severity": inc["severity"], "title": inc["title"],
            "src": self._party(inc["src_ip"], isolated), "dst": self._party(inc["dst_ip"], isolated),
            "facts": inc["facts"] or {}, "count": inc["count"],
            "first_seen": inc["first_seen"], "last_seen": inc["last_seen"],
            "status": inc["status"], "isolated_by": inc["isolated_by"], "isolated_at": inc["isolated_at"],
            "isolation_mode": inc["isolation_mode"], "note": inc["note"],
            "explanation": inc["explanation"], "steps": inc["steps"] or [], "reported": bool(inc["reported"]),
        }

    def status(self):
        isolated = self.store.isolated_ips()
        incidents = [self.incident_view(i, isolated) for i in self.store.list_incidents(100)]
        devices = []
        for d in self.store.list_devices():
            devices.append({
                "ip": d["ip"], "name": d["name"] or self.detector.device_name(d["ip"]),
                "kind": d["kind"], "zone": d["zone"], "mac": d["mac"], "vendor": d["vendor"],
                "first_seen": d["first_seen"], "last_seen": d["last_seen"], "source": d["source"],
                "isolated": d["ip"] in isolated,
            })
        with self._integrity_lock:
            integrity = dict(self._integrity)
        recent = [{"seq": e["seq"], "time": e["time"], "kind": e["kind"], "text": describe(e)} for e in self.evidence.tail(8)]
        recent.reverse()
        return {
            "box": {"name": self.cfg["box_name"], "unit": self.cfg["unit"], "operator": self.cfg["operator"],
                    "version": __version__, "now": time.time()},
            "links": {"blokir": self.responder.mode, "ai": self.explainer.state, "ai_model": self.explainer.model,
                      "perilaku": self.detector.watcher.status(self.detector.learning_active())},
            "learning": {"active": self.detector.learning_active(), "until": self.detector.learning_until},
            "sensor": {"eve_path": str(self.cfg.eve_path), "lines_read": self.tailer.lines_read},
            "incidents": incidents,
            "devices": devices,
            "evidence": {"code": self.evidence.code(), "count": self.evidence.count,
                         "integrity": integrity, "recent": recent},
        }

    def report_entries(self, incident_id):
        return [
            {"seq": e["seq"], "time": e["time"], "text": describe(e)}
            for e in self.evidence.entries()
            if (e.get("data") or {}).get("incident") == incident_id
        ]
