"""Tebakan merek perangkat dari 3 byte awal alamat MAC (OUI).

Daftar ini sengaja kecil. Tambahkan sendiri merek yang ada di markas Anda.
Daftar lengkap ada di situs IEEE (cari "IEEE OUI list").
"""

OUI = {
    "08:00:27": "VirtualBox",
    "00:50:56": "VMware",
    "00:0c:29": "VMware",
    "52:54:00": "QEMU/KVM",
    "4c:5e:0c": "MikroTik",
    "6c:3b:6b": "MikroTik",
    "48:8f:5a": "MikroTik",
    "64:d1:54": "MikroTik",
    "cc:2d:e0": "MikroTik",
    "d4:ca:6d": "MikroTik",
    "b8:69:f4": "MikroTik",
    "e4:8d:8c": "MikroTik",
    "44:19:b6": "Hikvision",
    "c0:56:e3": "Hikvision",
    "bc:ad:28": "Hikvision",
    "28:57:be": "Hikvision",
    "3c:ef:8c": "Dahua",
    "90:02:a9": "Dahua",
    "e0:50:8b": "Dahua",
    "24:0a:c4": "Espressif",
    "30:ae:a4": "Espressif",
    "24:6f:28": "Espressif",
    "a4:cf:12": "Espressif",
    "c8:2b:96": "Espressif",
    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
    "50:c7:bf": "TP-Link",
    "14:cc:20": "TP-Link",
    "f4:f2:6d": "TP-Link",
}


def lookup(mac):
    if not mac:
        return None
    return OUI.get(mac.lower()[:8])
