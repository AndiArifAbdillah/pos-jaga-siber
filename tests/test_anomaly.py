import random
import unittest
from pathlib import Path

from pjs import config
from pjs.anomaly import BehaviorWatcher, IsolationForest, c_factor

ROOT = Path(__file__).resolve().parent.parent


class EmptyStore:
    def __init__(self):
        self.samples = []

    def list_samples(self, zone):
        return [f for z, f in self.samples if z == zone]


class IsolationForestTest(unittest.TestCase):
    def test_c_factor(self):
        self.assertEqual(c_factor(1), 0.0)
        self.assertEqual(c_factor(2), 1.0)
        self.assertAlmostEqual(c_factor(256), 10.24, places=1)

    def test_outlier_scores_higher(self):
        rng = random.Random(1)
        rows = [[rng.gauss(0, 1), rng.gauss(0, 1)] for _ in range(500)]
        forest = IsolationForest(trees=100, sample_size=256).fit(rows)
        inlier = forest.score([0.0, 0.0])
        outlier = forest.score([6.0, -6.0])
        self.assertLess(inlier, 0.5)
        self.assertGreater(outlier, 0.65)

    def test_same_seed_same_result(self):
        rows = [[i % 7, i % 5] for i in range(300)]
        a = IsolationForest(seed=3).fit(rows).score([20, 20])
        b = IsolationForest(seed=3).fit(rows).score([20, 20])
        self.assertEqual(a, b)


class BehaviorWatcherTest(unittest.TestCase):
    def setUp(self):
        cfg = config.load(ROOT / "config.demo.json")
        self.watcher = BehaviorWatcher(cfg["anomaly"], EmptyStore(), cfg.base_dir)
        self.watcher.train()

    def score(self, zone, **feats):
        base = {"flows": 1, "destinations": 1, "ports": 1, "bytes_out": 3000, "bytes_in": 3000, "external": 0, "hour": 14}
        return self.watcher.evaluate(zone, {**base, **feats})

    def test_models_trained_from_seed(self):
        self.assertEqual(sorted(self.watcher.models), ["it", "ot"])
        self.assertEqual(self.watcher.status(learning=False)["state"], "aktif")

    def test_normal_samples_are_not_flagged(self):
        for zone in ("ot", "it"):
            flagged = [r for r in self.watcher.training_rows(zone) if self.watcher.evaluate(zone, r)[0] >= self.watcher.threshold]
            self.assertEqual(flagged, [], zone)

    def test_scanning_device_is_flagged_with_reason(self):
        score, reason = self.score("ot", flows=14, destinations=14, ports=4, bytes_out=1080, bytes_in=360)
        self.assertGreaterEqual(score, self.watcher.high)
        self.assertIn("14 perangkat atau alamat berbeda", reason)

    def test_equipment_talking_outside_is_flagged(self):
        score, reason = self.score("ot", bytes_out=48_000_000, bytes_in=61_000, external=1)
        self.assertGreaterEqual(score, self.watcher.high)
        self.assertIn("luar markas", reason)

    def test_busy_office_laptop_is_normal(self):
        score, _ = self.score("it", flows=12, destinations=6, ports=2, bytes_out=80_000, bytes_in=2_000_000, external=8)
        self.assertLess(score, self.watcher.threshold)

    def test_windows_close_after_window_and_grace(self):
        w = self.watcher
        t = 1_000_000.0
        w.observe("10.20.0.40", "ot", False, "10.20.0.5", 80, 100, 50, t)
        w.observe("10.20.0.40", "ot", False, "10.20.0.10", 502, 100, 50, t + 1)
        self.assertEqual(w.due(t + 5), [])
        done = w.due(t + w.window_s + 5)
        self.assertEqual(len(done), 1)
        ip, zone, feats, _ = done[0]
        self.assertEqual((ip, zone, feats["flows"], feats["destinations"], feats["ports"]), ("10.20.0.40", "ot", 2, 2, 2))

    def test_no_model_without_enough_samples(self):
        watcher = BehaviorWatcher({"min_samples": 200}, EmptyStore())
        watcher.train()
        self.assertIsNone(watcher.evaluate("ot", {"flows": 1}))
        self.assertEqual(watcher.status(learning=False)["state"], "kurang_data")
        self.assertEqual(watcher.status(learning=True)["state"], "belajar")


if __name__ == "__main__":
    unittest.main()
