"""Asisten piket dengan AI lokal.

Dua tugas:
1. Tanya kotak: petugas bertanya dengan bahasa sehari-hari ("ada apa dengan
   kamera gudang semalam?"). Kotak mencari kejadian dan perangkat yang cocok,
   lalu AI menjawab HANYA dari data itu. Nomor kejadian yang disebut AI
   diperiksa; nomor yang tidak ada di data dibuang.
2. Laporan ganti piket: ringkasan kejadian selama piket, siap disalin ke buku
   jaga. Daftar kejadian dan angka selalu diambil langsung dari data. AI hanya
   menulis paragraf ringkasannya.

Kalau AI tidak tersedia, kedua tugas tetap berjalan tanpa AI: tanya kotak
menampilkan hasil pencarian, laporan memakai ringkasan bawaan.
"""

import re
import time
from datetime import datetime

from .explainer import STYLE, _clean

SEVERITY_LABEL = {"kritis": "Kritis", "tinggi": "Tinggi", "sedang": "Sedang", "rendah": "Rendah"}
STATUS_LABEL = {
    "menunggu": "menunggu keputusan",
    "diisolasi": "diisolasi",
    "dilepas": "isolasi dilepas",
    "bukan_ancaman": "ditandai bukan ancaman",
}
ZONE_LABEL = {"ot": "peralatan", "it": "kantor", "other": "internal lain"}
ID_PATTERN = re.compile(r"PJS-\d{4,}", re.IGNORECASE)
STOPWORDS = {
    "apa", "ada", "yang", "dan", "atau", "dengan", "dari", "ke", "di", "ini", "itu", "saja", "sudah",
    "belum", "apakah", "bagaimana", "kenapa", "mengapa", "kapan", "berapa", "mana", "siapa", "tolong",
    "hari", "tadi", "semalam", "sekarang", "terjadi", "kejadian", "perangkat", "sedang", "untuk",
}


def _clock(ts):
    return datetime.fromtimestamp(ts).strftime("%H.%M") if ts else "-"


def _stamp(ts):
    return datetime.fromtimestamp(ts).strftime("%d-%m-%Y %H.%M") if ts else "-"


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in STOPWORDS}


class ShiftAssistant:
    def __init__(self, app):
        self.app = app

    # --- bahan dari data kotak ------------------------------------------
    def _incident_line(self, inc):
        names = self.app.detector.names(inc["src_ip"], inc["dst_ip"], inc["facts"])
        exp = inc.get("explanation") or {}
        line = (
            f"{inc['id']} | {_stamp(inc['first_seen'])} s.d. {_clock(inc['last_seen'])} | "
            f"{SEVERITY_LABEL.get(inc['severity'], inc['severity'])} | {STATUS_LABEL.get(inc['status'], inc['status'])} | "
            f"{inc['title']} | dari {names['src']} ke {names['dst']} | terjadi {inc['count']} kali | {exp.get('what', '')}"
        )
        if (inc.get("facts") or {}).get("ml_score") is not None:
            line += f" | skor keanehan AI {inc['facts']['ml_score']}"
        return line

    def _device_line(self, device, isolated):
        name = device["name"] or self.app.detector.device_name(device["ip"])
        seen = _stamp(device["last_seen"]) if device["last_seen"] else "belum terlihat"
        # Hanya status sambungan jaringan. Kotak tidak tahu keadaan fisik perangkat,
        # jadi jangan menulis "normal" yang bisa dibaca AI sebagai "genset baik-baik saja".
        status = "sedang diisolasi dari jaringan" if device["ip"] in isolated else "tidak diisolasi"
        return f"{name} | {device['ip']} | jaringan {ZONE_LABEL.get(device['zone'], 'luar')} | terakhir terlihat {seen} | {status}"

    def retrieve(self, question, limit=8):
        """Cari kejadian dan perangkat yang paling cocok dengan pertanyaan."""
        wanted_ids = {m.upper() for m in ID_PATTERN.findall(question)}
        words = _words(question)
        incidents = self.app.store.list_incidents(200)
        isolated = self.app.store.isolated_ips()
        lines = [(inc, self._incident_line(inc)) for inc in incidents]

        # Kata yang jarang muncul (misalnya "kamera") lebih berarti daripada kata umum (misalnya "utama").
        seen_in = {}
        for _, line in lines:
            for word in _words(line) & words:
                seen_in[word] = seen_in.get(word, 0) + 1

        def score(text):
            return sum(1 / seen_in.get(w, 1) for w in words & _words(text))

        scored = [(score(line) + (10 if inc["id"] in wanted_ids else 0), inc["last_seen"] or 0, inc["id"], line)
                  for inc, line in lines]
        matched = [s for s in scored if s[0] > 0]
        chosen = sorted(matched or scored, key=lambda s: (s[0], s[1]), reverse=True)[:limit]

        devices = []
        for device in self.app.store.list_devices():
            line = self._device_line(device, isolated)
            if score(line) > 0 or device["ip"] in question:
                devices.append(line)
        best = chosen[0][0] if chosen and matched else 0
        return [(c[2], c[3], c[0] >= 0.5 * best) for c in chosen], devices[:limit]

    # --- tanya kotak ----------------------------------------------------
    def ask(self, question, operator=None):
        question = " ".join(str(question).split())[:300]
        if not question:
            return {"ok": False, "message": "Pertanyaan kosong."}
        incidents, devices = self.retrieve(question)
        known_ids = {i for i, _, _ in incidents}
        result = None
        explainer = self.app.explainer
        if explainer.usable:
            try:
                answer = explainer.generate(self._ask_prompt(question, incidents, devices), timeout=90)
                text = _clean(answer.get("jawaban", ""), limit=900)
                sources = [s.upper() for s in answer.get("sumber", []) if isinstance(s, str)]
                if "tidak menemukan" in text.lower():
                    sources = []
                if text:
                    result = {
                        "ok": True, "mode": "ai", "model": explainer.model, "answer": text,
                        "sources": [s for s in dict.fromkeys(sources) if s in known_ids],
                    }
                    explainer.state = "siap"
            except Exception:
                explainer.state = "tidak_tersambung"
        if result is None:
            result = self._search_answer(incidents, devices)
        self.app.evidence.append("tanya_kotak", {
            "question": question, "operator": operator, "mode": result["mode"], "sources": result["sources"],
        })
        return result

    def _ask_prompt(self, question, incidents, devices):
        data = "\n".join(line for _, line, _ in incidents) or "(tidak ada kejadian tercatat)"
        dev = "\n".join(devices) or "(tidak ada perangkat yang cocok)"
        return f"""Kamu asisten petugas jaga di markas satuan TNI AD. Petugas ini bukan ahli komputer.
Jawab pertanyaan petugas HANYA berdasarkan DATA di bawah.

Aturan:
- {STYLE}
- Tanpa istilah teknis, paling banyak 5 kalimat.
- Kalau jawabannya tidak ada di DATA, jawab: "Saya tidak menemukan datanya di catatan kotak." dengan "sumber": [].
- Sebut nomor kejadian (misalnya PJS-0002) yang kamu pakai.
- Jangan mengarang kejadian, waktu, atau perangkat yang tidak ada di DATA.
- Jangan menyarankan tindakan selain yang sudah tertulis di DATA.
Jawab hanya dengan JSON: {{"jawaban": "...", "sumber": ["PJS-...."]}}

Waktu sekarang: {_stamp(time.time())}

DATA KEJADIAN (nomor | waktu | tingkat | status | judul | dari-ke | jumlah | penjelasan):
{data}

DATA PERANGKAT (nama | alamat | jaringan | terakhir terlihat | status isolasi). Kotak tidak tahu keadaan fisik perangkat:
{dev}

PERTANYAAN PETUGAS: {question}
"""

    @staticmethod
    def _search_answer(incidents, devices):
        """Jawaban tanpa AI: daftar catatan yang paling cocok."""
        top = [(i, line) for i, line, strong in incidents if strong][:3]
        if top:
            parts = []
            for _, line in top:
                p = line.split(" | ")
                parts.append(f"{p[0]} ({p[3]}): {p[4]}")
            text = "Catatan yang paling cocok: " + "; ".join(parts) + "."
        elif devices:
            text = "Perangkat yang cocok: " + "; ".join(devices[:3]) + "."
        else:
            text = "Tidak ada catatan yang cocok dengan pertanyaan ini."
        return {"ok": True, "mode": "pencarian", "model": None, "answer": text, "sources": [i for i, _ in top]}

    # --- laporan ganti piket --------------------------------------------
    def shift_report(self, hours=8, operator=None):
        hours = max(1, min(int(hours), 72))
        now = time.time()
        since = now - hours * 3600
        incidents = [i for i in self.app.store.list_incidents(500) if (i["last_seen"] or 0) >= since]
        incidents.sort(key=lambda i: i["first_seen"] or 0)
        counts = {s: sum(1 for i in incidents if i["severity"] == s) for s in ("kritis", "tinggi", "sedang", "rendah")}
        waiting = [i for i in incidents if i["status"] == "menunggu"]
        isolated = [i for i in incidents if i["status"] == "diisolasi"]
        new_devices = [d for d in self.app.store.list_devices() if d["source"] == "baru" and (d["first_seen"] or 0) >= since]
        integrity = self.app.evidence.verify()
        code = self.app.evidence.code()

        summary = self._template_summary(hours, incidents, counts, waiting, isolated)
        mode, model = "templat", None
        explainer = self.app.explainer
        if explainer.usable and incidents:
            try:
                answer = explainer.generate(self._report_prompt(hours, incidents, waiting, isolated, integrity), timeout=90)
                text = _clean(answer.get("ringkasan", ""), limit=700)
                if text:
                    summary, mode, model = text, "ai", explainer.model
                    explainer.state = "siap"
            except Exception:
                explainer.state = "tidak_tersambung"

        cfg = self.app.cfg
        lines = [
            f"LAPORAN GANTI PIKET - {cfg['box_name']} - {cfg['unit']}",
            f"Periode : {_stamp(since)} s.d. {_stamp(now)} ({hours} jam)",
            f"Petugas : {operator or cfg['operator']}",
            "",
            "Ringkasan" + (" (disusun AI lokal):" if mode == "ai" else ":"),
            summary,
            "",
            f"Kejadian ({len(incidents)}):",
        ]
        if incidents:
            for inc in incidents:
                lines.append(f"- {inc['id']} [{SEVERITY_LABEL.get(inc['severity'])}] {inc['title']} - "
                             f"{STATUS_LABEL.get(inc['status'], inc['status'])}, {_clock(inc['first_seen'])}")
        else:
            lines.append("- Tidak ada kejadian.")
        lines += ["", "Perlu ditindaklanjuti piket berikutnya:"]
        lines += [f"- {i['id']} {i['title']} (menunggu keputusan)" for i in waiting] or ["- Tidak ada."]
        if new_devices:
            lines += ["", "Perangkat baru terlihat:"]
            lines += [f"- {d['ip']} {d['vendor'] or ''}".rstrip() for d in new_devices]
        lines += [
            "",
            f"Catatan bukti : {'UTUH' if integrity['ok'] else 'PUTUS - ' + integrity['message']}, {self.app.evidence.count} entri",
            f"Kode buku jaga: {code}",
        ]
        self.app.evidence.append("laporan_piket", {"hours": hours, "operator": operator, "mode": mode, "code": code})
        return {"ok": True, "mode": mode, "model": model, "text": "\n".join(lines)}

    @staticmethod
    def _template_summary(hours, incidents, counts, waiting, isolated):
        if not incidents:
            return f"Selama {hours} jam terakhir tidak ada kejadian. Jaringan markas berjalan normal."
        parts = [f"{counts[s]} {s}" for s in ("kritis", "tinggi", "sedang", "rendah") if counts[s]]
        text = f"Selama {hours} jam terakhir tercatat {len(incidents)} kejadian ({', '.join(parts)})."
        if isolated:
            text += f" {len(isolated)} perangkat masih diisolasi."
        text += f" {len(waiting)} kejadian masih menunggu keputusan." if waiting else " Semua kejadian sudah ditangani."
        return text

    def _report_prompt(self, hours, incidents, waiting, isolated, integrity):
        data = "\n".join(self._incident_line(i) for i in incidents)
        return f"""Kamu asisten petugas jaga di markas satuan TNI AD.
Tulis ringkasan ganti piket untuk {hours} jam terakhir, 2 sampai 4 kalimat, tanpa istilah teknis.
{STYLE}
Sebut hal paling penting dulu, lalu apa yang masih harus ditindaklanjuti piket berikutnya.
Jangan mengarang kejadian atau angka yang tidak ada di DATA.
Jawab hanya dengan JSON: {{"ringkasan": "..."}}

DATA KEJADIAN:
{data}

Masih menunggu keputusan: {len(waiting)}. Masih diisolasi: {len(isolated)}.
Catatan bukti: {"utuh" if integrity["ok"] else "PUTUS"}.
"""
