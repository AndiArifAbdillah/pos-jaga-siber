"""Penjelas kejadian dalam bahasa sehari-hari.

1. Penjelasan bawaan (templat) langsung tersedia saat kejadian muncul.
2. Kalau Ollama aktif, AI lokal menyusun ulang "apa" dan "kenapa" agar lebih
   pas dengan kejadiannya. Hasil AI menggantikan templat setelah siap.
3. Langkah tindakan TIDAK pernah dibuat AI. Langkah selalu dari playbook (SOP).
4. AI tidak bisa memblokir apa pun. Ia hanya menerima teks dan membalas teks.
"""

import json
import queue
import threading
import urllib.error
import urllib.request

from . import playbook

ZONE_LABEL = {"ot": "jaringan peralatan", "it": "jaringan kantor", "other": "jaringan internal lain", None: "luar markas"}
STATUS_LABEL = {
    "menunggu": "menunggu keputusan petugas",
    "diisolasi": "sudah diisolasi",
    "dilepas": "isolasi sudah dilepas",
    "bukan_ancaman": "ditandai bukan ancaman",
}


STYLE = (
    "Pakai bahasa Indonesia yang sederhana, jelas, dan sopan, seperti laporan petugas kepada atasan. "
    'Jangan memakai bahasa gaul atau singkatan percakapan seperti "gak", "nggak", "udah", atau "matiin".'
)


def template(incident, names):
    entry = playbook.get(incident["kind"])
    return {
        "what": playbook.fill(entry["what"], **names),
        "why": playbook.fill(entry["why"], **names),
        "source": "templat",
        "model": None,
        "pending": False,
    }


def steps(kind, names):
    return [{"text": playbook.fill(s, **names), "checked": False} for s in playbook.get(kind)["steps"]]


def build_prompt(incident, names, zones):
    facts = incident.get("facts") or {}
    step_lines = "\n".join(f"{i}. {s['text']}" for i, s in enumerate(incident.get("steps") or [], start=1))
    lines = [
        f"- Judul: {incident['title']}",
        f"- Tingkat bahaya: {incident['severity']}",
        f"- Dari: {names['src']} ({ZONE_LABEL.get(zones[0], 'luar markas')})",
    ]
    # Kejadian tanpa tujuan (perangkat baru, perilaku tidak biasa) tidak boleh diberi
    # baris "Ke", supaya AI tidak mengira ada sambungan ke luar markas.
    if incident.get("dst_ip"):
        lines.append(f"- Ke: {names['dst']} ({ZONE_LABEL.get(zones[1], 'luar markas')})")
    lines += [
        f"- Terjadi: {incident.get('count', 1)} kali",
        f"- Status: {STATUS_LABEL.get(incident.get('status'), incident.get('status'))}",
    ]
    if facts.get("signature"):
        lines.append(f"- Catatan sensor: {facts['signature']}")
    if facts.get("ml_score") is not None:
        lines.append(f"- Temuan AI deteksi perilaku (skor keanehan {facts['ml_score']} dari 1): perangkat {facts.get('ml_reason', '-')}")
    data = "\n".join(lines)
    return f"""Kamu membantu petugas jaga di markas satuan TNI AD. Petugas ini bukan ahli komputer.
Tulis penjelasan singkat tentang kejadian jaringan di bawah ini.
{STYLE}

Aturan:
- Jangan memakai istilah teknis seperti alamat IP, port, protokol, Modbus, malware, atau payload. Sebut perangkat dengan namanya.
- "apa": satu atau dua kalimat tentang apa yang terjadi.
- "kenapa": satu atau dua kalimat tentang bahaya bagi markas kalau kejadian seperti ini tidak ditangani.
- Jangan menulis langkah tindakan. Langkah sudah ditetapkan SOP di bawah.
- Jangan menambah fakta yang tidak ada di data.
Jawab hanya dengan JSON: {{"apa": "...", "kenapa": "..."}}

Data kejadian:
{data}

Langkah SOP yang akan dibaca petugas:
{step_lines}
"""


def _clean(text, limit=420):
    text = " ".join(str(text).split())
    return text[:limit].rstrip()


class Explainer:
    def __init__(self, cfg, on_ready, on_failed):
        self.enabled = bool(cfg.get("enabled"))
        self.url = cfg.get("url", "http://127.0.0.1:11434").rstrip("/")
        self.model = cfg.get("model")
        self.timeout = float(cfg.get("timeout_s", 120))
        self.on_ready, self.on_failed = on_ready, on_failed
        self.state = "mati" if not self.enabled else "memeriksa"
        self._queue = queue.Queue()

    def start(self):
        if not self.enabled:
            return
        models = self.list_models()
        if models is None:
            self.state = "tidak_tersambung"
        elif not self.has_model(models):
            self.state = "model_tidak_ada"
        else:
            self.state = "memuat"
            threading.Thread(target=self._warm_up, name="pemanas-ai", daemon=True).start()
        threading.Thread(target=self._worker, name="penjelas-ai", daemon=True).start()

    @property
    def usable(self):
        """AI boleh dicoba. Model yang belum diunduh tidak dicoba sama sekali."""
        return self.enabled and self.state != "model_tidak_ada"

    def list_models(self):
        """Nama model yang sudah diunduh di Ollama, atau None kalau Ollama tidak bisa dihubungi."""
        try:
            with urllib.request.urlopen(self.url + "/api/tags", timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (OSError, ValueError, urllib.error.URLError):
            return None
        return [m.get("name", "") for m in data.get("models", [])]

    def has_model(self, models):
        wanted = self.model if ":" in self.model else self.model + ":latest"
        return wanted in models

    def ping(self):
        return self.list_models() is not None

    def _warm_up(self):
        """Muat model ke memori sejak kotak menyala. Permintaan pertama ke model
        yang belum dimuat bisa butuh puluhan detik; setelah dimuat cukup beberapa detik."""
        body = json.dumps({"model": self.model, "prompt": "", "keep_alive": "30m"}).encode("utf-8")
        req = urllib.request.Request(self.url + "/api/generate", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read()
            if self.state == "memuat":
                self.state = "siap"
        except (OSError, urllib.error.URLError):
            self.state = "tidak_tersambung"

    def request(self, incident_id, prompt):
        """Masukkan ke antrean. Hasil `True` kalau permintaan diterima."""
        if not self.usable:
            return False
        self._queue.put((incident_id, prompt))
        return True

    def _worker(self):
        while True:
            incident_id, prompt = self._queue.get()
            try:
                result = self.ask(prompt)
                self.state = "siap"
                self.on_ready(incident_id, result)
            except Exception as exc:  # AI gagal tidak boleh menghentikan kotak
                self.state = "tidak_tersambung"
                self.on_failed(incident_id, str(exc))

    def generate(self, prompt, timeout=None):
        """Kirim prompt ke Ollama dan kembalikan jawaban JSON sebagai dict.
        Dipakai juga oleh asisten piket (assistant.py)."""
        body = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {"temperature": 0.2},
        }).encode("utf-8")
        req = urllib.request.Request(self.url + "/api/generate", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
        answer = json.loads(reply.get("response", "{}"))
        if not isinstance(answer, dict):
            raise ValueError("Jawaban AI bukan JSON objek.")
        return answer

    def ask(self, prompt):
        answer = self.generate(prompt)
        what, why = _clean(answer.get("apa", "")), _clean(answer.get("kenapa", ""))
        if not what or not why:
            raise ValueError("Jawaban AI tidak lengkap.")
        return {"what": what, "why": why, "source": "ai", "model": self.model, "pending": False}
