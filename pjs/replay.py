"""Memutar ulang contoh catatan Suricata ke berkas eve.json.

Dipakai untuk mencoba kotak tanpa Suricata, misalnya di laptop Windows.
Waktu setiap catatan diganti dengan waktu sekarang supaya terasa nyata.

Baris khusus di berkas contoh:
  {"_bab": "Judul skenario"}   penanda awal skenario (mode --langkah menunggu Enter)
  {"_jeda": 2, ...}            jeda sebelum catatan ini ditulis (detik)
"""

import json
import time
from datetime import datetime
from pathlib import Path


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def replay(source, target, delay_s=0.3, chapter_pause_s=4.0, step=False, out=print, stop_event=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = Path(source).read_text(encoding="utf-8").splitlines()
    written = 0
    with open(target, "a", encoding="utf-8") as f:
        for line in lines:
            if stop_event is not None and stop_event.is_set():
                break
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            event = json.loads(line)
            if "_bab" in event:
                out(f"\n=== {event['_bab']} ===")
                if step:
                    input("Tekan Enter untuk memutar skenario ini... ")
                else:
                    time.sleep(chapter_pause_s)
                continue
            time.sleep(float(event.pop("_jeda", delay_s)))
            now = _now_iso()
            event["timestamp"] = now
            if isinstance(event.get("flow"), dict):
                event["flow"]["start"] = now
                event["flow"]["end"] = now
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
            written += 1
            label = (event.get("alert") or {}).get("signature") or event.get("event_type")
            out(f"  {event.get('src_ip')} -> {event.get('dest_ip')}  {label}")
    return written
