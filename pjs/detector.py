"""Otak kotak: mengubah catatan Suricata menjadi kejadian, lalu memutuskan tindakan.

Alur satu catatan (lihat docs/belajar/09-tur-kode.md):
  1. Catat perangkat yang terlihat (daftar perangkat / inventaris).
  2. Kalau catatan berupa peringatan Suricata: tentukan jenis dan tingkatnya.
     Kalau berupa lalu lintas biasa: cek aturan dasar (peralatan ke luar, sinyal berkala).
  3. Buat kejadian baru, atau tambah hitungan kejadian yang masih terbuka.
  4. Kritis + menyangkut peralatan (OT) -> isolasi otomatis dulu, baru dijelaskan.
     Selain itu -> dijelaskan, lalu petugas yang memutuskan.
  5. Setiap langkah ditulis ke catatan bukti.

Selain itu, setiap sambungan dicatat untuk AI deteksi perilaku (anomaly.py).
Setiap rentang waktu yang selesai dinilai lewat flush_behavior().
"""

import itertools
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime

from . import explainer as expl
from . import playbook, vendors
from .anomaly import BehaviorWatcher

_TZ_NO_COLON = re.compile(r"([+-]\d\d)(\d\d)$")
_ids = itertools.count(1)


def parse_ts(value):
    """Ubah waktu Suricata ('2026-11-12T15:20:01.123456+0700') menjadi detik epoch."""
    if not value:
        return time.time()
    text = str(value).strip()
    text = text[:-1] + "+00:00" if text.endswith("Z") else _TZ_NO_COLON.sub(r"\1:\2", text)
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return time.time()


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


class Detector:
    def __init__(self, cfg, store, evidence, responder, explainer):
        self.cfg, self.store, self.evidence = cfg, store, evidence
        self.responder, self.explainer = responder, explainer
        self._lock = threading.RLock()
        self._last_write = {}
        self._beacon_flows = OrderedDict()
        self._beacon_reported = set()
        started = store.meta_get("learning_started")
        if started is None:
            started = time.time()
            store.meta_set("learning_started", started)
        self.learning_started = float(started)
        self._load_configured_devices()
        self.watcher = BehaviorWatcher(cfg["anomaly"], store, cfg.base_dir)
        self._last_train = 0.0
        if not self.learning_active():
            self._train_behavior()

    # --- bantuan --------------------------------------------------------
    @property
    def learning_until(self):
        return self.learning_started + float(self.cfg["learning_hours"]) * 3600

    def learning_active(self):
        return time.time() < self.learning_until

    def _load_configured_devices(self):
        for ip, conf in self.cfg.devices.items():
            fields = {"name": conf.get("name"), "kind": conf.get("kind"), "zone": self.cfg.zone_of(ip)}
            if conf.get("mac"):
                fields.update(mac=conf["mac"].lower(), vendor=vendors.lookup(conf["mac"]))
            if self.store.get_device(ip):
                self.store.update_device(ip, **fields)
            else:
                self.store.add_device({"ip": ip, **fields, "first_seen": None, "last_seen": None, "source": "konfigurasi"})

    def device_name(self, ip):
        if not ip:
            return "-"
        conf = self.cfg.devices.get(ip)
        if conf and conf.get("name"):
            return conf["name"]
        device = self.store.get_device(ip)
        if device and device.get("name"):
            return device["name"]
        if self.cfg.is_internal(ip):
            vendor = device.get("vendor") if device else None
            return f"Perangkat tak dikenal {ip}" + (f" ({vendor})" if vendor else "")
        return f"alamat {ip}"

    def names(self, src_ip, dst_ip, facts=None):
        return {
            "src": self.device_name(src_ip),
            "dst": self.device_name(dst_ip),
            "signature": (facts or {}).get("signature") or "Kejadian mencurigakan",
            "reason": (facts or {}).get("reason") or "",
        }

    # --- pintu masuk ----------------------------------------------------
    def process(self, event):
        if not isinstance(event, dict):
            return
        event_type = event.get("event_type")
        if event_type in (None, "stats"):
            return
        with self._lock:
            ts = parse_ts(event.get("timestamp"))
            ether = event.get("ether") or {}
            self._see_device(event.get("src_ip"), ether.get("src_mac"), ts)
            if self._destination_answered(event):
                self._see_device(event.get("dest_ip"), ether.get("dest_mac"), ts)
            if event_type == "alert":
                self._on_alert(event, ts)
            else:
                self._on_traffic(event, ts)

    # --- daftar perangkat -----------------------------------------------
    @staticmethod
    def _destination_answered(event):
        """Alamat tujuan dianggap perangkat nyata hanya kalau ia membalas.

        Pemindai mencoba banyak alamat kosong. Tanpa pemeriksaan ini, setiap alamat
        kosong yang dicoba akan tercatat sebagai "perangkat baru".
        """
        flow = event.get("flow")
        if event.get("event_type") == "flow" and isinstance(flow, dict) and "pkts_toclient" in flow:
            return (flow.get("pkts_toclient") or 0) > 0
        return True

    def _see_device(self, ip, mac, ts):
        if not ip or not self.cfg.is_device_address(ip):
            return
        mac = (mac or "").lower() or None
        if mac in self.cfg.router_macs or mac == "ff:ff:ff:ff:ff:ff":
            mac = None
        known = self.store.get_device(ip)
        now = time.time()
        if known is None:
            learning = self.learning_active()
            self.store.add_device({
                "ip": ip, "mac": mac, "vendor": vendors.lookup(mac), "name": None, "kind": None,
                "zone": self.cfg.zone_of(ip), "first_seen": ts, "last_seen": ts,
                "source": "masa_belajar" if learning else "baru",
            })
            self._last_write[ip] = now
            if not learning:
                self._raise("perangkat_baru", None, ip, "", {"mac": mac, "vendor": vendors.lookup(mac)}, ts)
            return
        updates = {}
        if mac and not known.get("mac"):
            updates.update(mac=mac, vendor=vendors.lookup(mac))
        if known.get("first_seen") is None:
            updates["first_seen"] = ts
        if known.get("last_seen") is None or now - self._last_write.get(ip, 0) > 30:
            updates["last_seen"] = ts
        if updates:
            self._last_write[ip] = now
            self.store.update_device(ip, **updates)

    # --- peringatan Suricata --------------------------------------------
    def _on_alert(self, event, ts):
        alert = event.get("alert") or {}
        meta = alert.get("metadata") or {}
        kind, severity = _first(meta.get("pjs_jenis")), _first(meta.get("pjs_tingkat"))
        sid = alert.get("signature_id")
        if not kind and sid in playbook.SID_FALLBACK:
            kind, severity = playbook.SID_FALLBACK[sid]
        if not kind:
            level = int(alert.get("severity") or 3)
            if level > int(self.cfg["suricata_lowest_severity"]):
                return
            kind, severity = f"umum:{sid}", {1: "tinggi", 2: "sedang"}.get(level, "rendah")
        if severity not in playbook.SEVERITY_ORDER:
            severity = None
        facts = {
            "signature": alert.get("signature"),
            "sid": sid,
            "app_proto": event.get("app_proto"),
            "dest_port": event.get("dest_port"),
            "interface": event.get("in_iface"),
        }
        self._raise(kind, severity, event.get("src_ip"), event.get("dest_ip") or "", facts, ts)

    # --- aturan dasar dari lalu lintas biasa ----------------------------
    def _on_traffic(self, event, ts):
        src, dst = event.get("src_ip"), event.get("dest_ip")
        if not src or not dst:
            return
        zone = self.cfg.zone_of(src)
        external = self.cfg.is_external(dst)
        if event.get("event_type") == "flow":
            flow = event.get("flow") or {}
            self.watcher.observe(src, zone, external, dst, event.get("dest_port"),
                                 flow.get("bytes_toserver"), flow.get("bytes_toclient"), ts)
        if not external:
            return
        if zone == "ot":
            facts = {"dest_port": event.get("dest_port"), "app_proto": event.get("app_proto")}
            out = (event.get("flow") or {}).get("bytes_toserver")
            if out is not None:
                facts["bytes_out"] = out
            self._raise("ot_ke_luar", None, src, dst, facts, ts)
        elif zone in ("it", "other"):
            self._track_beacon(src, dst, event, ts)

    def _track_beacon(self, src, dst, event, ts):
        """Sinyal berkala: sambungan ke alamat luar yang sama dengan jarak waktu nyaris sama."""
        key = (src, dst)
        if key in self._beacon_reported:
            return
        flow = event.get("flow") or {}
        start = parse_ts(flow["start"]) if flow.get("start") else ts
        flow_id = event.get("flow_id") or f"tanpa-id-{next(_ids)}"
        seen = self._beacon_flows.setdefault(key, OrderedDict())
        self._beacon_flows.move_to_end(key)
        while len(self._beacon_flows) > 5000:
            self._beacon_flows.popitem(last=False)
        if flow_id in seen:
            return
        seen[flow_id] = start
        while len(seen) > 30:
            seen.popitem(last=False)
        rule = self.cfg["beacon"]
        times = sorted(seen.values())[-int(rule["min_count"]):]
        if len(times) < int(rule["min_count"]):
            return
        gaps = [later - earlier for earlier, later in zip(times, times[1:])]
        mean = sum(gaps) / len(gaps)
        if not rule["min_interval_s"] <= mean <= rule["max_interval_s"]:
            return
        if (max(gaps) - min(gaps)) / mean > rule["max_jitter"]:
            return
        self._beacon_reported.add(key)
        facts = {"interval_s": round(mean, 1), "jumlah": len(seen), "dest_port": event.get("dest_port")}
        self._raise("sinyal_berkala", None, src, dst, facts, ts)

    # --- AI deteksi perilaku --------------------------------------------
    def _train_behavior(self):
        self._last_train = time.time()
        self.watcher.train()

    def flush_behavior(self, now=None):
        """Nilai rentang waktu yang sudah selesai. Dipanggil kotak setiap detik."""
        now = now if now is not None else time.time()
        with self._lock:
            learning = self.learning_active()
            if not learning and not self.watcher.models and time.time() - self._last_train > 600:
                self._train_behavior()
            for ip, zone, feats, start in self.watcher.due(now):
                if learning:
                    self.store.add_sample(zone, start, feats)
                    continue
                result = self.watcher.evaluate(zone, feats)
                if result is None:
                    continue
                score, reason = result
                if score >= self.watcher.threshold:
                    self._raise_behavior(ip, score, reason, start + self.watcher.window_s)

    def _raise_behavior(self, ip, score, reason, ts):
        """Perilaku aneh. Kalau perangkat ini sudah punya kejadian terbuka dari aturan lain,
        skor AI ditempelkan ke kejadian itu sebagai penguat, bukan kejadian baru."""
        score = round(score, 2)
        existing = self.store.find_open_incident_by_src(ip)
        if existing:
            facts = existing["facts"] or {}
            if score > facts.get("ml_score", 0):
                facts.update(ml_score=score, ml_reason=reason)
                self.store.update_incident(existing["id"], facts=facts)
            if existing["kind"] != "perilaku_aneh":
                return existing["id"]
        severity = "tinggi" if score >= self.watcher.high else "sedang"
        facts = {"ml_score": score, "ml_reason": reason, "reason": reason, "window_s": self.watcher.window_s}
        return self._raise("perilaku_aneh", severity, ip, "", facts, ts)

    # --- kejadian -------------------------------------------------------
    def _raise(self, kind, severity, src, dst, facts, ts):
        dst = dst or ""
        if self.store.is_suppressed(kind, src, dst):
            return None
        existing = self.store.find_open_incident(kind, src, dst)
        if existing:
            self.store.update_incident(existing["id"], count=existing["count"] + 1, last_seen=max(ts, existing["last_seen"]))
            return existing["id"]
        entry = playbook.get(kind)
        severity = severity or entry["severity"]
        names = self.names(src, dst, facts)
        incident_id = self.store.next_incident_id()
        incident = {
            "id": incident_id, "kind": kind, "severity": severity,
            "title": playbook.fill(entry["title"], **names),
            "src_ip": src, "dst_ip": dst, "facts": facts,
            "first_seen": ts, "last_seen": ts, "count": 1, "status": "menunggu",
            "explanation": None, "steps": expl.steps(kind, names),
        }
        incident["explanation"] = expl.template(incident, names)
        self.store.add_incident(incident)
        self.evidence.append("kejadian_baru", {
            "incident": incident_id, "kind": kind, "severity": severity,
            "title": incident["title"], "src": src, "dst": dst,
        })
        if self._should_auto_isolate(severity, src, dst):
            self.isolate(incident_id, by="otomatis")
        self._ask_ai(incident_id)
        return incident_id

    def _should_auto_isolate(self, severity, src, dst):
        if severity != "kritis" or not self.cfg["auto_isolate"]:
            return False
        if src in self.cfg.never_isolate:
            return False
        return "ot" in (self.cfg.zone_of(src), self.cfg.zone_of(dst))

    # --- tindakan (dari aturan otomatis atau tombol petugas) ------------
    def isolate(self, incident_id, by="operator", operator=None):
        with self._lock:
            inc = self.store.get_incident(incident_id)
            if not inc:
                return False, "Kejadian tidak ditemukan."
            if inc["status"] == "diisolasi":
                return True, "Perangkat ini sudah diisolasi."
            target = inc["src_ip"]
            if not target or target in self.cfg.never_isolate:
                return False, f"{self.device_name(target)} termasuk perangkat yang tidak boleh diisolasi."
            ok, message = self.responder.isolate(target, comment=f"{incident_id} {by}")
            data = {"incident": incident_id, "ip": target, "mode": self.responder.mode, "operator": operator}
            if ok:
                self.store.update_incident(
                    incident_id, status="diisolasi", isolated_ip=target, isolated_by=by,
                    isolated_at=time.time(), isolation_mode=self.responder.mode, note=message,
                )
                self.evidence.append("isolasi_otomatis" if by == "otomatis" else "isolasi_operator", data)
            else:
                self.store.update_incident(incident_id, note=message)
                self.evidence.append("isolasi_gagal", {**data, "message": message})
            return ok, message

    def release(self, incident_id, operator=None):
        with self._lock:
            inc = self.store.get_incident(incident_id)
            if not inc or inc["status"] != "diisolasi":
                return False, "Kejadian ini tidak sedang diisolasi."
            ip = inc["isolated_ip"]
            others = [i for i in self.store.incidents_isolating(ip) if i != incident_id]
            if others:
                ok, message = True, f"{ip} tetap diisolasi karena kejadian {', '.join(others)}."
            else:
                ok, message = self.responder.release(ip)
            if not ok:
                self.store.update_incident(incident_id, note=message)
                return False, message
            self.store.update_incident(incident_id, status="dilepas", note=message)
            self.evidence.append("isolasi_dilepas", {"incident": incident_id, "ip": ip, "operator": operator})
            return True, message

    def dismiss(self, incident_id, operator=None):
        """Tombol 'Bukan ancaman': kejadian serupa tidak dibunyikan lagi."""
        with self._lock:
            inc = self.store.get_incident(incident_id)
            if not inc:
                return False, "Kejadian tidak ditemukan."
            if inc["status"] == "diisolasi":
                ok, message = self.release(incident_id, operator)
                if not ok:
                    return False, message
            self.store.add_suppression(inc["kind"], inc["src_ip"], inc["dst_ip"], operator)
            self.store.update_incident(incident_id, status="bukan_ancaman", note="Kejadian serupa tidak akan dibunyikan lagi.")
            self.evidence.append("bukan_ancaman", {"incident": incident_id, "operator": operator})
            return True, "Ditandai bukan ancaman."

    def reopen(self, incident_id, operator=None):
        with self._lock:
            inc = self.store.get_incident(incident_id)
            if not inc:
                return False, "Kejadian tidak ditemukan."
            self.store.remove_suppression(inc["kind"], inc["src_ip"], inc["dst_ip"])
            self._beacon_reported.discard((inc["src_ip"], inc["dst_ip"]))
            self.store.update_incident(incident_id, status="menunggu", note="Dibuka lagi oleh petugas.")
            self.evidence.append("dibuka_lagi", {"incident": incident_id, "operator": operator})
            return True, "Kejadian dibuka lagi."

    def set_step(self, incident_id, index, checked, operator=None):
        with self._lock:
            inc = self.store.get_incident(incident_id)
            steps = (inc or {}).get("steps") or []
            if not 0 <= index < len(steps):
                return False, "Langkah tidak ditemukan."
            steps[index]["checked"] = bool(checked)
            self.store.update_incident(incident_id, steps=steps)
            self.evidence.append("langkah_dicentang" if checked else "langkah_dibatalkan", {
                "incident": incident_id, "step": index + 1, "text": steps[index]["text"], "operator": operator,
            })
            return True, "Langkah dicatat."

    def mark_reported(self, incident_id, operator=None):
        with self._lock:
            if not self.store.get_incident(incident_id):
                return False, "Kejadian tidak ditemukan."
            self.store.update_incident(incident_id, reported=1)
            self.evidence.append("laporan_dibuat", {"incident": incident_id, "operator": operator})
            return True, "Laporan dibuat."

    # --- penjelasan AI --------------------------------------------------
    def _ask_ai(self, incident_id):
        inc = self.store.get_incident(incident_id)
        names = self.names(inc["src_ip"], inc["dst_ip"], inc["facts"])
        zones = (self.cfg.zone_of(inc["src_ip"]), self.cfg.zone_of(inc["dst_ip"]) if inc["dst_ip"] else None)
        if self.explainer.request(incident_id, expl.build_prompt(inc, names, zones)):
            self.store.update_incident(incident_id, explanation={**inc["explanation"], "pending": True})

    def apply_explanation(self, incident_id, explanation):
        with self._lock:
            self.store.update_incident(incident_id, explanation=explanation)
            self.evidence.append("penjelasan_ai", {
                "incident": incident_id, "model": explanation["model"],
                "what": explanation["what"], "why": explanation["why"],
            })

    def explanation_failed(self, incident_id, reason):
        with self._lock:
            inc = self.store.get_incident(incident_id)
            if inc:
                explanation = {**inc["explanation"], "pending": False, "error": reason[:200]}
                self.store.update_incident(incident_id, explanation=explanation)
