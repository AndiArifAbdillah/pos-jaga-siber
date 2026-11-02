"""Penyimpanan SQLite: perangkat, kejadian (insiden), penekanan alarm, dan info kecil lain.

Satu koneksi dipakai bersama oleh beberapa thread, jadi setiap akses dijaga kunci.
"""

import json
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    ip TEXT PRIMARY KEY,
    mac TEXT,
    vendor TEXT,
    name TEXT,
    kind TEXT,
    zone TEXT,
    first_seen REAL,
    last_seen REAL,
    source TEXT
);
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    kind TEXT,
    severity TEXT,
    title TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    facts TEXT,
    first_seen REAL,
    last_seen REAL,
    count INTEGER,
    status TEXT,
    isolated_ip TEXT,
    isolated_by TEXT,
    isolated_at REAL,
    isolation_mode TEXT,
    note TEXT,
    explanation TEXT,
    steps TEXT,
    reported INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS suppressions (
    kind TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    created_at REAL,
    operator TEXT,
    PRIMARY KEY (kind, src_ip, dst_ip)
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

OPEN_STATUSES = ("menunggu", "diisolasi")
JSON_FIELDS = ("facts", "explanation", "steps")


class Store:
    def __init__(self, path):
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()

    def close(self):
        with self._lock:
            self._db.close()

    def _run(self, sql, args=()):
        with self._lock:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur

    def _all(self, sql, args=()):
        with self._lock:
            return [dict(row) for row in self._db.execute(sql, args).fetchall()]

    def _one(self, sql, args=()):
        rows = self._all(sql, args)
        return rows[0] if rows else None

    # --- info kecil -----------------------------------------------------
    def meta_get(self, key, default=None):
        row = self._one("SELECT value FROM meta WHERE key = ?", (key,))
        return row["value"] if row else default

    def meta_set(self, key, value):
        self._run("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, str(value)))

    # --- perangkat ------------------------------------------------------
    def get_device(self, ip):
        return self._one("SELECT * FROM devices WHERE ip = ?", (ip,))

    def add_device(self, device):
        cols = ", ".join(device)
        marks = ", ".join("?" for _ in device)
        self._run(f"INSERT OR IGNORE INTO devices ({cols}) VALUES ({marks})", tuple(device.values()))

    def update_device(self, ip, **fields):
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._run(f"UPDATE devices SET {sets} WHERE ip = ?", (*fields.values(), ip))

    def list_devices(self):
        return self._all("SELECT * FROM devices ORDER BY zone, ip")

    # --- kejadian -------------------------------------------------------
    def next_incident_id(self):
        with self._lock:
            row = self._db.execute("SELECT value FROM meta WHERE key = 'incident_counter'").fetchone()
            number = int(row["value"]) + 1 if row else 1
            self._db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('incident_counter', ?)", (str(number),))
            self._db.commit()
        return f"PJS-{number:04d}"

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        for field in JSON_FIELDS:
            row[field] = json.loads(row[field]) if row.get(field) else None
        return row

    def add_incident(self, incident):
        row = {k: (json.dumps(v, ensure_ascii=False) if k in JSON_FIELDS else v) for k, v in incident.items()}
        cols = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        self._run(f"INSERT INTO incidents ({cols}) VALUES ({marks})", tuple(row.values()))

    def update_incident(self, incident_id, **fields):
        row = {k: (json.dumps(v, ensure_ascii=False) if k in JSON_FIELDS else v) for k, v in fields.items()}
        sets = ", ".join(f"{k} = ?" for k in row)
        self._run(f"UPDATE incidents SET {sets} WHERE id = ?", (*row.values(), incident_id))

    def get_incident(self, incident_id):
        return self._decode(self._one("SELECT * FROM incidents WHERE id = ?", (incident_id,)))

    def find_open_incident(self, kind, src_ip, dst_ip):
        marks = ", ".join("?" for _ in OPEN_STATUSES)
        return self._decode(
            self._one(
                f"SELECT * FROM incidents WHERE kind = ? AND src_ip = ? AND dst_ip = ? "
                f"AND status IN ({marks}) ORDER BY first_seen DESC LIMIT 1",
                (kind, src_ip, dst_ip, *OPEN_STATUSES),
            )
        )

    def list_incidents(self, limit=100):
        rows = self._all("SELECT * FROM incidents ORDER BY last_seen DESC LIMIT ?", (limit,))
        return [self._decode(r) for r in rows]

    def isolated_ips(self):
        rows = self._all("SELECT isolated_ip, id FROM incidents WHERE status = 'diisolasi' AND isolated_ip IS NOT NULL")
        return {r["isolated_ip"]: r["id"] for r in rows}

    def incidents_isolating(self, ip):
        rows = self._all("SELECT id FROM incidents WHERE status = 'diisolasi' AND isolated_ip = ?", (ip,))
        return [r["id"] for r in rows]

    # --- penekanan alarm ("Bukan ancaman") ------------------------------
    def add_suppression(self, kind, src_ip, dst_ip, operator):
        self._run(
            "INSERT OR REPLACE INTO suppressions (kind, src_ip, dst_ip, created_at, operator) VALUES (?, ?, ?, ?, ?)",
            (kind, src_ip, dst_ip, time.time(), operator),
        )

    def remove_suppression(self, kind, src_ip, dst_ip):
        self._run("DELETE FROM suppressions WHERE kind = ? AND src_ip = ? AND dst_ip = ?", (kind, src_ip, dst_ip))

    def is_suppressed(self, kind, src_ip, dst_ip):
        return (
            self._one(
                "SELECT 1 AS x FROM suppressions WHERE kind = ? AND src_ip = ? AND dst_ip = ?",
                (kind, src_ip, dst_ip),
            )
            is not None
        )
