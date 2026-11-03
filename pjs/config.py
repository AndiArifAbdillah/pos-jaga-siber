"""Membaca berkas konfigurasi kotak.

Semua nilai punya bawaan (DEFAULTS). Berkas konfigurasi cukup berisi nilai
yang ingin diubah saja. Jalur berkas (data_dir, eve_path) dihitung relatif
terhadap folder tempat berkas konfigurasi berada.
"""

import copy
import ipaddress
import json
from pathlib import Path

DEFAULTS = {
    "box_name": "Pos Jaga Siber",
    "unit": "Satuan contoh",
    "operator": "Operator jaga",
    "data_dir": "data",
    "eve_path": "/var/log/suricata/eve.json",
    "read_from_start": False,
    "web": {"host": "0.0.0.0", "port": 8080},
    # Jaringan milik markas. "ot" = peralatan, "it" = komputer kantor,
    # "other" = jaringan internal lain yang bukan "luar".
    "networks": {"ot": ["10.20.0.0/24"], "it": ["10.10.0.0/24"], "other": []},
    # Perangkat yang sudah dikenal: ip, name, kind, zone (opsional), mac (opsional).
    "devices": [],
    # Alamat yang tidak boleh diisolasi, misalnya router dan kotak ini sendiri.
    "never_isolate": [],
    # MAC milik router. Paket yang dirutekan membawa MAC router, jadi MAC ini
    # tidak boleh ditempelkan ke perangkat lain.
    "router_macs": [],
    # Lama masa belajar (jam). Selama masa belajar, perangkat baru dicatat diam-diam.
    "learning_hours": 336,
    "auto_isolate": True,
    # Peringatan Suricata umum (tanpa metadata PJS) diproses kalau tingkatnya
    # 1 sampai nilai ini. Suricata: 1 paling berat, 3 paling ringan.
    "suricata_lowest_severity": 2,
    "beacon": {"min_count": 6, "min_interval_s": 10, "max_interval_s": 3600, "max_jitter": 0.2},
    # AI deteksi perilaku (Isolation Forest). window_s = panjang satu rentang waktu.
    # Skor >= threshold menjadi kejadian sedang, >= high menjadi kejadian tinggi.
    # seed_file = contoh perilaku normal dari berkas (dipakai demo), relatif ke folder konfigurasi.
    "anomaly": {
        "enabled": True,
        "window_s": 300,
        "threshold": 0.62,
        "high": 0.72,
        "min_samples": 200,
        "trees": 100,
        "sample_size": 256,
        "seed_file": None,
    },
    "mikrotik": {
        "enabled": False,
        "host": "10.10.0.1",
        "port": 8728,
        "user": "pjs",
        "password": "",
        "address_list": "pjs-karantina",
        "timeout": "24h",
    },
    "ollama": {
        "enabled": False,
        "url": "http://127.0.0.1:11434",
        "model": "qwen2.5:1.5b",
        "timeout_s": 120,
    },
}


def _merge(base, extra):
    """Gabungkan dua dict secara mendalam. List dan nilai biasa diganti utuh."""
    result = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Config:
    def __init__(self, data, base_dir):
        self.raw = data
        self.base_dir = Path(base_dir)
        self.data_dir = self._path(data["data_dir"])
        self.eve_path = self._path(data["eve_path"])
        nets = data["networks"]
        self.ot_nets = [ipaddress.ip_network(n, strict=False) for n in nets.get("ot", [])]
        self.it_nets = [ipaddress.ip_network(n, strict=False) for n in nets.get("it", [])]
        self.other_nets = [ipaddress.ip_network(n, strict=False) for n in nets.get("other", [])]
        self.devices = {d["ip"]: d for d in data["devices"]}
        self.never_isolate = set(data["never_isolate"])
        self.router_macs = {m.lower() for m in data["router_macs"]}

    def __getitem__(self, key):
        return self.raw[key]

    def _path(self, value):
        path = Path(value)
        return path if path.is_absolute() else (self.base_dir / path).resolve()

    @staticmethod
    def _ip(value):
        try:
            return ipaddress.ip_address(value)
        except (TypeError, ValueError):
            return None

    def zone_of(self, ip):
        """'ot', 'it', 'other', atau None kalau alamatnya di luar markas."""
        device = self.devices.get(ip)
        if device and device.get("zone"):
            return device["zone"]
        addr = self._ip(ip)
        if addr is None:
            return None
        for zone, nets in (("ot", self.ot_nets), ("it", self.it_nets), ("other", self.other_nets)):
            if any(addr in net for net in nets):
                return zone
        return None

    def is_internal(self, ip):
        return self.zone_of(ip) is not None

    def is_external(self, ip):
        """Alamat unicast yang bukan milik markas, misalnya alamat di internet."""
        addr = self._ip(ip)
        if addr is None or addr.is_multicast or addr.is_loopback or addr.is_link_local or addr.is_unspecified:
            return False
        if str(addr) == "255.255.255.255":
            return False
        return not self.is_internal(ip)

    def is_device_address(self, ip):
        """Alamat yang pantas dicatat sebagai perangkat (bukan alamat siaran)."""
        addr = self._ip(ip)
        if addr is None or addr.is_multicast or addr.is_unspecified:
            return False
        for net in self.ot_nets + self.it_nets + self.other_nets:
            if addr in net:
                return addr != net.broadcast_address and addr != net.network_address
        return False


def load(path=None, overrides=None):
    data = copy.deepcopy(DEFAULTS)
    base_dir = Path.cwd()
    if path:
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = _merge(data, json.load(f))
        base_dir = path.resolve().parent
    if overrides:
        data = _merge(data, overrides)
    return Config(data, base_dir)
