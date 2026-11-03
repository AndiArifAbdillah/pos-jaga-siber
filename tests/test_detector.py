import json
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

from pjs import config
from pjs.detector import Detector, parse_ts
from pjs.evidence import EvidenceLog
from pjs.store import Store

ROOT = Path(__file__).resolve().parent.parent


class FakeResponder:
    mode = "uji"

    def __init__(self):
        self.isolated, self.released = [], []

    def isolate(self, ip, comment):
        self.isolated.append(ip)
        return True, "ok"

    def release(self, ip):
        self.released.append(ip)
        return True, "ok"


class FakeExplainer:
    def __init__(self):
        self.prompts = []

    def request(self, incident_id, prompt):
        self.prompts.append((incident_id, prompt))
        return True


def sample_events():
    events = []
    for line in (ROOT / "lab" / "contoh_eve.jsonl").read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if "_bab" not in event:
            event.pop("_jeda", None)
            events.append(event)
    return events


class DetectorTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.cfg = config.load(ROOT / "config.demo.json")
        self.store = Store(base / "pjs.sqlite3")
        self.evidence = EvidenceLog(base / "bukti.jsonl", base / "kunci.key")
        self.responder = FakeResponder()
        self.explainer = FakeExplainer()
        self.detector = Detector(self.cfg, self.store, self.evidence, self.responder, self.explainer)

    def tearDown(self):
        self.store.close()
        self.dir.cleanup()

    def play(self, events, start=None, step_s=2.0):
        """Putar catatan dengan waktu buatan yang berjarak tetap."""
        t = start or time.time()
        for event in events:
            stamp = datetime.fromtimestamp(t).astimezone().isoformat(timespec="microseconds")
            event = dict(event, timestamp=stamp)
            if "flow" in event:
                event["flow"] = dict(event["flow"], start=stamp)
            self.detector.process(event)
            t += step_s

    def incidents(self):
        return {i["kind"]: i for i in self.store.list_incidents()}

    def test_sample_creates_expected_incidents(self):
        self.play(sample_events())
        found = self.incidents()
        self.assertEqual(set(found), {"perangkat_baru", "ot_tulis", "ot_ke_luar", "sinyal_berkala"})
        genset = found["ot_tulis"]
        self.assertEqual(genset["severity"], "kritis")
        self.assertEqual(genset["status"], "diisolasi")
        self.assertEqual(genset["isolated_by"], "otomatis")
        self.assertEqual(genset["count"], 3)
        self.assertEqual(self.responder.isolated, ["10.10.0.66"])
        self.assertEqual(found["ot_ke_luar"]["status"], "menunggu")
        self.assertEqual(found["sinyal_berkala"]["src_ip"], "10.10.0.23")
        self.assertTrue(self.evidence.verify()["ok"])

    def test_router_mac_is_not_given_to_other_devices(self):
        self.play(sample_events())
        attacker = self.store.get_device("10.10.0.66")
        self.assertEqual(attacker["mac"], "02:42:ac:66:00:66")
        self.assertIsNone(self.store.get_device("10.10.0.1")["mac"])

    def test_not_a_threat_suppresses_repeats(self):
        self.play(sample_events())
        camera = self.incidents()["ot_ke_luar"]
        ok, _ = self.detector.dismiss(camera["id"], operator="Uji")
        self.assertTrue(ok)
        before = len(self.store.list_incidents())
        self.play([e for e in sample_events() if e.get("src_ip") == "10.20.0.21" and e.get("dest_ip") == "203.0.113.50"])
        self.assertEqual(len(self.store.list_incidents()), before)
        self.assertEqual(self.store.get_incident(camera["id"])["status"], "bukan_ancaman")

    def test_operator_isolate_and_release(self):
        self.play(sample_events())
        camera = self.incidents()["ot_ke_luar"]
        ok, _ = self.detector.isolate(camera["id"], operator="Serda Uji")
        self.assertTrue(ok)
        self.assertIn("10.20.0.21", self.responder.isolated)
        ok, _ = self.detector.release(camera["id"], operator="Serda Uji")
        self.assertTrue(ok)
        self.assertEqual(self.responder.released, ["10.20.0.21"])
        kinds = [e["kind"] for e in self.evidence.entries()]
        self.assertIn("isolasi_operator", kinds)
        self.assertIn("isolasi_dilepas", kinds)

    def test_never_isolate_router(self):
        event = {"event_type": "alert", "src_ip": "10.20.0.1", "dest_ip": "10.20.0.10", "dest_port": 502,
                 "alert": {"signature_id": 1990001, "signature": "uji", "severity": 1}}
        self.play([event])
        inc = self.incidents()["ot_tulis"]
        self.assertEqual(inc["status"], "menunggu")
        self.assertEqual(self.responder.isolated, [])

    def test_irregular_traffic_is_not_a_beacon(self):
        base = time.time()
        events = []
        for n, gap in enumerate([3, 41, 7, 90, 12, 60, 5]):
            base += gap
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(base)) + ".000000+0700"
            events.append({"event_type": "flow", "flow_id": 900 + n, "src_ip": "10.10.0.21", "dest_ip": "198.51.100.9",
                           "dest_port": 443, "timestamp": stamp, "flow": {"start": stamp}})
        for event in events:
            self.detector.process(event)
        self.assertNotIn("sinyal_berkala", self.incidents())

    def test_steps_are_logged(self):
        self.play(sample_events())
        genset = self.incidents()["ot_tulis"]
        ok, _ = self.detector.set_step(genset["id"], 0, True, operator="Serda Uji")
        self.assertTrue(ok)
        self.assertTrue(self.store.get_incident(genset["id"])["steps"][0]["checked"])
        self.assertEqual(self.evidence.entries()[-1]["kind"], "langkah_dicentang")

    def test_ai_prompt_has_no_ip_and_keeps_sop(self):
        self.play(sample_events())
        _, prompt = next(p for p in self.explainer.prompts if "Genset" in p[1])
        self.assertIn("Jangan menulis langkah", prompt)
        self.assertIn("Genset utama", prompt)

    def test_parse_ts_formats(self):
        self.assertAlmostEqual(parse_ts("2026-11-12T15:20:01.123456+0700"), parse_ts("2026-11-12T15:20:01.123456+07:00"))
        self.assertAlmostEqual(parse_ts("2026-11-12T08:20:01Z"), parse_ts("2026-11-12T15:20:01+07:00"))

    # --- AI deteksi perilaku --------------------------------------------
    def test_ai_behavior_flags_scanning_door_without_blocking(self):
        start = time.time() - 3600
        self.play(sample_events(), start=start, step_s=0.1)
        self.detector.flush_behavior(start + 3600)
        odd = [i for i in self.store.list_incidents() if i["kind"] == "perilaku_aneh"]
        door = next(i for i in odd if i["src_ip"] == "10.20.0.40")
        self.assertGreaterEqual(door["facts"]["ml_score"], 0.72)
        self.assertEqual(door["severity"], "tinggi")
        self.assertEqual(door["status"], "menunggu")
        self.assertNotIn("10.20.0.40", self.responder.isolated)
        self.assertIn("perangkat atau alamat berbeda", door["explanation"]["what"])
        camera = self.incidents()["ot_ke_luar"]
        self.assertGreaterEqual(camera["facts"]["ml_score"], 0.72)
        self.assertFalse(any(i["src_ip"] == "10.20.0.21" for i in odd), "skor kamera harus menempel ke kejadian kamera")

    def test_scan_targets_that_do_not_answer_are_not_devices(self):
        self.play(sample_events())
        self.assertIsNone(self.store.get_device("10.20.0.11"))
        self.assertNotIn("perangkat_baru", {i["kind"] for i in self.store.list_incidents() if i["src_ip"] == "10.20.0.11"})

    def test_learning_collects_samples_instead_of_alerting(self):
        cfg = config.load(ROOT / "config.demo.json", overrides={"learning_hours": 1, "anomaly": {"seed_file": None}})
        store = Store(Path(self.dir.name) / "belajar.sqlite3")
        try:
            detector = Detector(cfg, store, self.evidence, FakeResponder(), FakeExplainer())
            start = time.time() - 600
            t = start
            for event in sample_events():
                stamp = datetime.fromtimestamp(t).astimezone().isoformat()
                detector.process(dict(event, timestamp=stamp))
                t += 0.1
            detector.flush_behavior(start + 600)
            self.assertGreater(len(store.list_samples("ot")), 0)
            self.assertNotIn("perilaku_aneh", {i["kind"] for i in store.list_incidents()})
            self.assertEqual(detector.watcher.status(detector.learning_active())["state"], "belajar")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
