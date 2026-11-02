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
    note = facts.get("signature") or "-"
    return f"""Kamu membantu petugas jaga di markas satuan TNI AD. Petugas ini bukan ahli komputer.
Tulis penjelasan singkat tentang kejadian jaringan di bawah ini dalam bahasa Indonesia sehari-hari.

Aturan:
- Jangan memakai istilah teknis seperti alamat IP, port, protokol, Modbus, malware, atau payload. Sebut perangkat dengan namanya.
- "apa": satu atau dua kalimat tentang apa yang terjadi.
- "kenapa": satu atau dua kalimat tentang kenapa ini berbahaya bagi markas.
- Jangan menulis langkah tindakan. Langkah sudah ditetapkan SOP di bawah.
- Jangan menambah fakta yang tidak ada di data.
Jawab hanya dengan JSON: {{"apa": "...", "kenapa": "..."}}

Data kejadian:
- Judul: {incident['title']}
- Tingkat bahaya: {incident['severity']}
- Dari: {names['src']} ({ZONE_LABEL.get(zones[0], 'luar markas')})
- Ke: {names['dst']} ({ZONE_LABEL.get(zones[1], 'luar markas')})
- Terjadi: {incident.get('count', 1)} kali
- Status: {STATUS_LABEL.get(incident.get('status'), incident.get('status'))}
- Catatan sensor: {note}

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
        self.state = "siap" if self.ping() else "tidak_tersambung"
        threading.Thread(target=self._worker, name="penjelas-ai", daemon=True).start()

    def ping(self):
        try:
            with urllib.request.urlopen(self.url + "/api/tags", timeout=2) as resp:
                return resp.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def request(self, incident_id, prompt):
        """Masukkan ke antrean. Hasil `True` kalau permintaan diterima."""
        if not self.enabled:
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

    def ask(self, prompt):
        body = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }).encode("utf-8")
        req = urllib.request.Request(self.url + "/api/generate", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
        answer = json.loads(reply.get("response", "{}"))
        what, why = _clean(answer.get("apa", "")), _clean(answer.get("kenapa", ""))
        if not what or not why:
            raise ValueError("Jawaban AI tidak lengkap.")
        return {"what": what, "why": why, "source": "ai", "model": self.model, "pending": False}
