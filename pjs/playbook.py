"""Daftar jenis kejadian: judul, tingkat bawaan, penjelasan bawaan, dan langkah SOP.

Langkah di sini adalah CONTOH. Sebelum dipakai sungguhan, ganti dengan SOP
resmi satuan. AI hanya boleh menjelaskan "apa" dan "kenapa"; langkah selalu
diambil dari daftar ini supaya petugas tidak menerima saran karangan AI.

Teks boleh memakai {src} (nama perangkat asal) dan {dst} (nama perangkat tujuan).
"""

SEVERITY_ORDER = {"kritis": 0, "tinggi": 1, "sedang": 2, "rendah": 3}

PLAYBOOK = {
    "ot_tulis": {
        "title": "Perintah asing ke {dst}",
        "severity": "kritis",
        "what": "{src} mengirim perintah untuk mengubah keadaan {dst}. Perangkat ini tidak terdaftar sebagai pengendali peralatan tersebut.",
        "why": "Kalau perintah seperti ini dibiarkan, peralatan bisa dimatikan atau diubah dari jarak jauh, misalnya genset mati tepat saat listrik PLN padam.",
        "steps": [
            "Periksa langsung panel {dst} dan pastikan peralatan masih bekerja normal.",
            "Biarkan {src} tetap terisolasi sampai pemiliknya diketahui.",
            "Cari tahu siapa pemilik {src} dan di ruangan mana perangkat itu berada.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
    "ot_baca_luar": {
        "title": "Ada yang mengintip {dst}",
        "severity": "tinggi",
        "what": "{src} dari luar jaringan peralatan membaca data dari {dst}. Biasanya hanya komputer pengendali yang melakukan ini.",
        "why": "Mengintip seperti ini sering menjadi tahap awal sebelum seseorang mencoba mengubah atau mematikan peralatan.",
        "steps": [
            "Cari tahu siapa pemilik {src} dan apa keperluannya.",
            "Kalau tidak ada yang mengaku, isolasi {src}.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
    "ot_telnet": {
        "title": "Percobaan masuk ke {dst}",
        "severity": "tinggi",
        "what": "{src} mencoba masuk ke {dst} lewat jalur pengaturan jarak jauh yang tidak aman.",
        "why": "Banyak peralatan masih memakai kata sandi bawaan pabrik. Kalau berhasil masuk, orang bisa mengambil alih peralatan itu.",
        "steps": [
            "Isolasi {src} kalau bukan petugas teknik yang sedang bekerja.",
            "Pastikan kata sandi {dst} sudah diganti dari bawaan pabrik.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
    "ot_ke_luar": {
        "title": "{src} mengirim data ke luar markas",
        "severity": "tinggi",
        "what": "{src} mengirim data ke {dst}, yaitu alamat di luar markas. Peralatan ini seharusnya hanya berkomunikasi di dalam markas.",
        "why": "Rekaman kamera atau data peralatan bisa bocor ke pihak luar, termasuk gambar tata letak dan kegiatan markas.",
        "steps": [
            "Isolasi {src} supaya tidak bisa mengirim keluar. Rekaman ke perekam lokal tetap berjalan.",
            "Catat merek dan tipe {src}, lalu periksa apakah ada pembaruan dari pabrik.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
    "sinyal_berkala": {
        "title": "{src} menghubungi alamat luar secara teratur",
        "severity": "tinggi",
        "what": "{src} berulang kali menghubungi {dst} di luar markas dengan jarak waktu yang sangat teratur, seperti jam yang berdetak.",
        "why": "Pola teratur seperti ini ciri khas program jahat yang melapor ke pengendalinya dan menunggu perintah.",
        "steps": [
            "Tanyakan ke pemakai {src} apakah ada program baru yang dipasang.",
            "Kalau tidak ada penjelasan yang wajar, isolasi {src}.",
            "Serahkan {src} ke petugas teknik untuk diperiksa. Jangan dimatikan dulu.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
    "perangkat_baru": {
        "title": "Ada perangkat baru di jaringan",
        "severity": "sedang",
        "what": "Perangkat yang belum pernah terlihat sebelumnya ({src}) mulai memakai jaringan markas.",
        "why": "Perangkat asing bisa milik tamu, tetapi juga bisa alat yang sengaja dipasang untuk menyusup.",
        "steps": [
            "Cari tahu pemilik perangkat ini dan keperluannya.",
            "Kalau sah, tekan Bukan ancaman supaya perangkat ini dikenali.",
            "Kalau tidak ada yang mengaku, isolasi perangkat ini.",
        ],
    },
    "umum": {
        "title": "{signature}",
        "severity": "sedang",
        "what": "Aturan umum sensor mencatat kejadian mencurigakan dari {src} ke {dst}.",
        "why": "Aturan ini dibuat dari pola serangan yang pernah terjadi di tempat lain.",
        "steps": [
            "Cari tahu pemilik {src}.",
            "Kalau ragu, isolasi {src} dan minta petugas teknik memeriksa.",
            "Laporkan ke penanggung jawab jaringan satuan sesuai SOP.",
        ],
    },
}

# Cadangan kalau Suricata tidak menulis metadata aturan ke eve.json.
SID_FALLBACK = {
    1990001: ("ot_tulis", "kritis"),
    1990002: ("ot_baca_luar", "tinggi"),
    1990003: ("ot_telnet", "tinggi"),
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def fill(text, **names):
    return text.format_map(_SafeDict(names))


def get(kind):
    return PLAYBOOK.get(kind, PLAYBOOK["umum"])
