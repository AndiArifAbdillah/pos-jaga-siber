"""AI deteksi perilaku: mengenali perangkat yang tiba-tiba berperilaku tidak biasa.

Aturan Suricata hanya menangkap pola serangan yang sudah dikenal. Modul ini
menangkap yang belum dikenal: kotak mempelajari kebiasaan perangkat selama
masa belajar, lalu memberi skor keanehan pada setiap rentang waktu.

Cara kerja (lihat docs/belajar/13-ai-deteksi-perilaku-dan-asisten.md):
1. Lalu lintas setiap perangkat dikelompokkan per rentang waktu (misalnya 5 menit).
2. Setiap rentang diringkas menjadi angka ciri: jumlah sambungan, jumlah tujuan,
   jumlah jenis layanan (port), data keluar, data masuk, sambungan ke luar markas, jam.
3. Selama masa belajar, ringkasan disimpan sebagai contoh "normal".
4. Setelah itu, kotak menilai setiap rentang dari dua sisi dan mengambil skor tertinggi:
   a. Pola gabungan: model Isolation Forest (machine learning) per jaringan
      (peralatan dan kantor). Skornya baru dihitung kalau lebih aneh daripada
      hampir semua contoh normal (dikalibrasi dari data latih sendiri).
   b. Batas kebiasaan per ciri: nilai yang melewati angka tertinggi yang pernah
      terlihat saat belajar. Ini menutup kelemahan Isolation Forest, yang
      mengabaikan ciri yang di data latih selalu sama (misalnya peralatan yang
      tidak pernah menghubungi luar markas).
   Jam aktif yang sangat jarang dipakai menambah skor ringan.
5. Skor di atas ambang menjadi kejadian "perilaku tidak biasa". Model ini
   TIDAK pernah memblokir sendiri; keputusan tetap di tangan petugas.

Isolation Forest ditulis dalam Python murni supaya kotak tidak perlu pustaka tambahan.
"""

import json
import math
import random
from datetime import datetime
from pathlib import Path

EULER = 0.5772156649

# Urutan ciri dalam vektor, dengan label untuk penjelasan.
FEATURES = ("flows", "destinations", "ports", "bytes_out", "bytes_in", "external")


def c_factor(n):
    """Rata-rata panjang jalur pencarian yang gagal di pohon biner berisi n data."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * (math.log(n - 1) + EULER) - 2.0 * (n - 1) / n


def to_vector(feats):
    """Ubah ringkasan mentah menjadi vektor angka untuk model.

    Dipakai logaritma, supaya 10 dan 100 sambungan berbeda jelas, tetapi
    1.000.000 dan 1.100.000 byte tidak dianggap jauh berbeda."""
    return [math.log1p(max(0.0, float(feats.get(k, 0)))) for k in FEATURES]


def range_score(exceed):
    """Ubah besarnya pelampauan batas menjadi skor 0,5–1."""
    return 0.5 + 0.5 * (1 - math.exp(-2 * exceed))


class IsolationForest:
    """Isolation Forest (Liu, Ting, Zhou, 2008).

    Gagasannya: data yang aneh lebih mudah "dipisahkan" dari kerumunan.
    Setiap pohon membelah data secara acak. Data aneh terpisah setelah sedikit
    belahan (jalurnya pendek), data normal butuh banyak belahan.
    """

    def __init__(self, trees=100, sample_size=256, seed=7):
        self.n_trees, self.max_samples, self.seed = trees, sample_size, seed
        self.trees, self.sample_size, self.norm = [], 0, 1.0

    def fit(self, rows):
        rng = random.Random(self.seed)
        self.sample_size = min(self.max_samples, len(rows))
        limit = math.ceil(math.log2(max(self.sample_size, 2)))
        self.trees = [self._build(rng.sample(rows, self.sample_size), 0, limit, rng) for _ in range(self.n_trees)]
        self.norm = c_factor(self.sample_size) or 1.0
        return self

    def _build(self, rows, depth, limit, rng):
        if depth >= limit or len(rows) <= 1:
            return ("daun", len(rows))
        dims = [d for d in range(len(rows[0])) if min(r[d] for r in rows) < max(r[d] for r in rows)]
        if not dims:
            return ("daun", len(rows))
        dim = rng.choice(dims)
        low, high = min(r[dim] for r in rows), max(r[dim] for r in rows)
        split = rng.uniform(low, high)
        left = [r for r in rows if r[dim] < split]
        right = [r for r in rows if r[dim] >= split]
        if not left or not right:
            return ("daun", len(rows))
        return ("cabang", dim, split, self._build(left, depth + 1, limit, rng), self._build(right, depth + 1, limit, rng))

    @staticmethod
    def _path_length(x, node):
        depth = 0
        while node[0] == "cabang":
            node = node[3] if x[node[1]] < node[2] else node[4]
            depth += 1
        return depth + c_factor(node[1])

    def score(self, x):
        """Skor keanehan 0–1. Sekitar 0,5 ke bawah = biasa, mendekati 1 = sangat aneh."""
        mean = sum(self._path_length(x, t) for t in self.trees) / len(self.trees)
        return 2 ** (-mean / self.norm)


def _percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[index]


def _format_bytes(n):
    for unit, size in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if n >= size:
            return f"{n / size:.1f} {unit}".replace(".", ",")
    return f"{int(n)} byte"


def _format_window(seconds):
    return f"{int(seconds // 60)} menit" if seconds >= 60 and seconds % 60 == 0 else f"{int(seconds)} detik"


class BehaviorWatcher:
    """Mengumpulkan ringkasan per perangkat, belajar, lalu menilai."""

    def __init__(self, cfg, store, base_dir=None):
        self.enabled = bool(cfg.get("enabled", True))
        self.window_s = float(cfg.get("window_s", 300))
        self.threshold = float(cfg.get("threshold", 0.62))
        self.high = float(cfg.get("high", 0.72))
        self.min_samples = int(cfg.get("min_samples", 200))
        self.trees = int(cfg.get("trees", 100))
        self.sample_size = int(cfg.get("sample_size", 256))
        self.store = store
        self.seed_rows = self._load_seed(cfg.get("seed_file"), base_dir)
        self.windows = {}
        self.models = {}
        self.stats = {}

    @staticmethod
    def _load_seed(path, base_dir):
        """Contoh perilaku normal dari berkas (dipakai demo). Hasil: {zona: [ringkasan, ...]}."""
        rows = {}
        if not path:
            return rows
        path = Path(path)
        if not path.is_absolute() and base_dir is not None:
            path = Path(base_dir) / path
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                item = json.loads(line)
                rows.setdefault(item["zone"], []).append(item["f"])
        return rows

    # --- mengumpulkan ---------------------------------------------------
    def observe(self, src, zone, dst_external, dst, dst_port, bytes_out, bytes_in, ts):
        """Catat satu sambungan (dari catatan flow Suricata) ke rentang waktunya."""
        if not self.enabled or zone not in ("ot", "it"):
            return
        start = math.floor(ts / self.window_s) * self.window_s
        window = self.windows.setdefault((src, start), {
            "zone": zone, "start": start, "flows": 0, "destinations": set(), "ports": set(),
            "bytes_out": 0, "bytes_in": 0, "external": 0,
        })
        window["flows"] += 1
        window["destinations"].add(dst)
        if dst_port is not None:
            window["ports"].add(dst_port)
        window["bytes_out"] += int(bytes_out or 0)
        window["bytes_in"] += int(bytes_in or 0)
        window["external"] += 1 if dst_external else 0

    def due(self, now, grace_s=2.0):
        """Ambil rentang yang sudah selesai. Hasil: [(ip, zona, ringkasan, waktu_mulai)]."""
        done = []
        for key in [k for k, w in self.windows.items() if now >= w["start"] + self.window_s + grace_s]:
            window = self.windows.pop(key)
            hour = datetime.fromtimestamp(window["start"]).hour
            feats = {
                "flows": window["flows"], "destinations": len(window["destinations"]),
                "ports": len(window["ports"]), "bytes_out": window["bytes_out"],
                "bytes_in": window["bytes_in"], "external": window["external"], "hour": hour,
            }
            done.append((key[0], window["zone"], feats, window["start"]))
        return done

    # --- belajar --------------------------------------------------------
    def training_rows(self, zone):
        return self.store.list_samples(zone) + self.seed_rows.get(zone, [])

    def train(self):
        """Latih satu model per jaringan yang contohnya sudah cukup."""
        for zone in ("ot", "it"):
            rows = self.training_rows(zone)
            if len(rows) < self.min_samples:
                continue
            vectors = [to_vector(r) for r in rows]
            model = IsolationForest(self.trees, self.sample_size).fit(vectors)
            train_scores = [model.score(v) for v in vectors]
            stats = {"count": len(rows), "hours": {}}
            for i, key in enumerate(FEATURES):
                logs = [v[i] for v in vectors]
                raw = [r.get(key, 0) for r in rows]
                stats[key] = {
                    "max_log": max(logs), "median_log": _percentile(logs, 0.5),
                    "max": max(raw), "median": _percentile(raw, 0.5),
                }
            for r in rows:
                hour = int(r.get("hour", 0))
                stats["hours"][hour] = stats["hours"].get(hour, 0) + 1
            # Skor Isolation Forest baru dihitung kalau lebih aneh daripada 99,5% contoh normal.
            stats["if_limit"] = _percentile(train_scores, 0.995) + 0.03
            self.models[zone], self.stats[zone] = model, stats

    # --- menilai --------------------------------------------------------
    def evaluate(self, zone, feats):
        """Hasil: (skor, alasan) atau None kalau model untuk jaringan ini belum ada."""
        model = self.models.get(zone)
        if model is None:
            return None
        stats = self.stats[zone]
        vec = to_vector(feats)
        over = []
        for i, key in enumerate(FEATURES):
            spread = max(stats[key]["max_log"] - stats[key]["median_log"], 0.5)
            exceed = (vec[i] - stats[key]["max_log"]) / spread
            if exceed > 0:
                over.append((range_score(exceed), key))
        if_score = model.score(vec)
        scores = [s for s, _ in over]
        if if_score > stats["if_limit"]:
            scores.append(if_score)
        rare_hour = self._rare_hour(stats, feats)
        if rare_hour:
            scores.append(0.64)
        # Tidak ada sisi yang menandai: skor tetap ditampilkan, tetapi di bawah ambang.
        score = max(scores) if scores else min(if_score, self.threshold - 0.01)
        return score, self.explain(zone, feats, [k for _, k in sorted(over, reverse=True)], rare_hour)

    @staticmethod
    def _rare_hour(stats, feats):
        hour = int(feats.get("hour", 0))
        return stats["count"] >= 200 and stats["hours"].get(hour, 0) < 0.005 * stats["count"]

    def explain(self, zone, feats, over_keys, rare_hour):
        """Ubah skor menjadi alasan yang bisa dibaca petugas."""
        stats = self.stats[zone]
        window = _format_window(self.window_s)
        phrases = []
        for key in over_keys[:3]:
            value, top = feats.get(key, 0), stats[key]["max"]
            usual = f"biasanya paling banyak {int(round(top))}" if top else "biasanya tidak pernah"
            if key == "flows":
                phrases.append(f"membuat {value} sambungan dalam {window} ({usual})")
            elif key == "destinations":
                phrases.append(f"menghubungi {value} perangkat atau alamat berbeda dalam {window} ({usual})")
            elif key == "ports":
                phrases.append(f"mencoba {value} jenis layanan berbeda ({usual})")
            elif key == "bytes_out":
                phrases.append(f"mengirim {_format_bytes(value)} dalam {window} (biasanya paling banyak {_format_bytes(top)})")
            elif key == "bytes_in":
                phrases.append(f"menerima {_format_bytes(value)} dalam {window} (biasanya paling banyak {_format_bytes(top)})")
            elif key == "external":
                phrases.append(f"menghubungi luar markas {value} kali ({usual})")
        if rare_hour:
            phrases.append(f"aktif pada jam {int(feats.get('hour', 0)):02d}.00 yang hampir tidak pernah dipakai")
        if not phrases:
            return "gabungan kegiatannya tidak cocok dengan kebiasaan perangkat di jaringan ini"
        if len(phrases) == 1:
            return phrases[0]
        return ", ".join(phrases[:-1]) + ", dan " + phrases[-1]

    def status(self, learning):
        if not self.enabled:
            return {"state": "mati"}
        counts = {z: len(self.training_rows(z)) for z in ("ot", "it")}
        if self.models:
            state = "aktif"
        elif learning:
            state = "belajar"
        else:
            state = "kurang_data"
        return {"state": state, "samples": counts, "zones": sorted(self.models), "min_samples": self.min_samples}
