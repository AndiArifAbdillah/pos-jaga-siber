import json
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

from pjs import config
from pjs.app import App

ROOT = Path(__file__).resolve().parent.parent


class AssistantTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        cfg = config.load(ROOT / "config.demo.json", overrides={
            "data_dir": str(base / "data"), "eve_path": str(base / "eve.json"), "ollama": {"enabled": False},
        })
        self.app = App(cfg)
        t = time.time() - 120
        for line in (ROOT / "lab" / "contoh_eve.jsonl").read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if "_bab" in event:
                continue
            event.pop("_jeda", None)
            event["timestamp"] = datetime.fromtimestamp(t).astimezone().isoformat()
            self.app.detector.process(event)
            t += 2

    def tearDown(self):
        self.app.store.close()
        self.dir.cleanup()

    def ids(self):
        return {i["kind"]: i["id"] for i in self.app.store.list_incidents()}

    def test_search_answer_without_ai(self):
        result = self.app.assistant.ask("ada apa dengan genset?", operator="Serda Uji")
        self.assertEqual(result["mode"], "pencarian")
        self.assertIn(self.ids()["ot_tulis"], result["sources"])
        self.assertIn("Genset", result["answer"])
        self.assertEqual(self.app.evidence.entries()[-1]["kind"], "tanya_kotak")

    def test_ai_answer_keeps_only_real_sources(self):
        prompts = []
        genset_id = self.ids()["ot_tulis"]

        def fake_generate(prompt, timeout=None):
            prompts.append(prompt)
            return {"jawaban": "Ada laptop asing yang mencoba mematikan genset, dan sudah diisolasi.", "sumber": [genset_id, "PJS-9999"]}

        self.app.explainer.enabled = True
        self.app.explainer.generate = fake_generate
        result = self.app.assistant.ask("ada apa dengan genset?")
        self.assertEqual(result["mode"], "ai")
        self.assertEqual(result["sources"], [genset_id])
        self.assertIn("HANYA berdasarkan DATA", prompts[0])
        self.assertIn("Genset utama", prompts[0])

    def test_not_found_answer_has_no_sources(self):
        self.app.explainer.enabled = True
        self.app.explainer.generate = lambda prompt, timeout=None: {
            "jawaban": "Saya tidak menemukan datanya di catatan kotak.", "sumber": [self.ids()["ot_tulis"]],
        }
        result = self.app.assistant.ask("berapa suhu ruang server?")
        self.assertEqual(result["sources"], [])

    def test_ai_failure_falls_back_to_search(self):
        def broken(prompt, timeout=None):
            raise OSError("Ollama mati")

        self.app.explainer.enabled = True
        self.app.explainer.generate = broken
        result = self.app.assistant.ask("kamera gerbang")
        self.assertEqual(result["mode"], "pencarian")
        self.assertIn(self.ids()["ot_ke_luar"], result["sources"])

    def test_shift_report_lists_facts_from_data(self):
        code_before = self.app.evidence.code()
        report = self.app.assistant.shift_report(8, operator="Serda Uji")
        text = report["text"]
        self.assertEqual(report["mode"], "templat")
        self.assertIn("LAPORAN GANTI PIKET", text)
        self.assertIn(self.ids()["ot_tulis"], text)
        self.assertIn("menunggu keputusan", text)
        self.assertIn(f"Kode buku jaga: {code_before}", text)
        self.assertEqual(self.app.evidence.entries()[-1]["kind"], "laporan_piket")

    def test_shift_report_uses_ai_summary(self):
        self.app.explainer.enabled = True
        self.app.explainer.generate = lambda prompt, timeout=None: {"ringkasan": "Piket ini ramai: genset sempat diserang."}
        report = self.app.assistant.shift_report(8)
        self.assertEqual(report["mode"], "ai")
        self.assertIn("Piket ini ramai", report["text"])
        self.assertIn(self.ids()["ot_tulis"], report["text"])


if __name__ == "__main__":
    unittest.main()
