# 06 · AI lokal: "mulut" kotak

Petugas jaga bukan ahli komputer. Pesan seperti `PJS OT perintah tulis Modbus dari perangkat yang bukan pengendali` tidak berarti apa-apa bagi mereka. Tugas AI di kotak ini satu saja: **menerjemahkan kejadian teknis menjadi bahasa sehari-hari.**

## 1. Apa itu model bahasa (LLM)

LLM (*large language model*) adalah program yang dilatih membaca teks dalam jumlah sangat besar, sampai ia pandai menebak **kata berikutnya** dalam sebuah kalimat. Dengan menebak kata demi kata, ia bisa menulis jawaban, ringkasan, atau penjelasan.

Hal penting tentang LLM:

- **Ia bisa salah dengan percaya diri.** Kadang ia mengarang fakta yang terdengar meyakinkan. Ini disebut **halusinasi**.
- **Ukuran model** dihitung dalam miliar parameter (B). Model 1–4B cukup kecil untuk laptop tanpa kartu grafis. Model besar seperti ChatGPT jauh lebih pintar, tetapi butuh pusat data dan internet.
- **Kuantisasi** memperkecil model dengan menyimpan angka secara lebih ringkas, misalnya 4 bit. Model 1,5B yang dikuantisasi butuh sekitar 1–2 GB RAM.

## 2. Kenapa harus lokal

| Alasan | Penjelasan |
|---|---|
| Data tidak keluar | Memakai AI di internet berarti mengirim informasi jaringan TNI ke server pihak lain, sering di luar negeri |
| Tetap jalan tanpa internet | Markas terpencil dan saat internet sengaja diputus penyerang |
| Tidak bergantung vendor | Tidak ada langganan, tidak bisa dimatikan pihak lain |

## 3. Ollama

**Ollama** adalah program gratis untuk menjalankan model bahasa di komputer sendiri. Setelah dipasang, ia melayani permintaan di `http://127.0.0.1:11434`.

```bash
ollama pull qwen2.5:1.5b             # unduh model (sekali saja, butuh internet)
ollama run qwen2.5:1.5b "Halo"       # coba bertanya langsung
ollama list                          # model yang sudah terpasang
```

Pilihan model (ukuran perkiraan, cek di situs Ollama untuk angka terbaru):

| Model | Unduhan | Cocok untuk |
|---|---|---|
| `qwen2.5:1.5b` | sekitar 1 GB | Laptop RAM 8 GB, jawaban cepat. **Bawaan proyek** |
| `llama3.2:3b` | sekitar 2 GB | Jawaban lebih rapi, lebih lambat |
| `gemma3:4b` | sekitar 3 GB | Bahasa Indonesia lebih baik, butuh RAM lebih |

Model diganti lewat `ollama.model` di berkas konfigurasi. Uji dengan `python -m pjs uji-ai`.

## 4. Cara kotak memakai AI

### Langkah demi langkah

1. Kejadian baru muncul. **Penjelasan bawaan** (templat dari `pjs/playbook.py`) langsung ditampilkan. Petugas tidak perlu menunggu AI.
2. Kotak menyusun **perintah (prompt)** untuk AI dan memasukkannya ke antrean.
3. Satu thread khusus (`Explainer._worker`) mengirim prompt ke Ollama.
4. Kalau jawaban sah, penjelasan bawaan **diganti** jawaban AI, dan dashboard menulis "Disusun AI lokal".
5. Kalau AI gagal atau tidak tersambung, penjelasan bawaan tetap tampil. Kotak tidak berhenti.

### Isi prompt

Lihat fungsi `build_prompt` di `pjs/explainer.py`. Bagian pentingnya:

```
Kamu membantu petugas jaga di markas satuan TNI AD. Petugas ini bukan ahli komputer.
...
- Jangan memakai istilah teknis seperti alamat IP, port, protokol, Modbus, malware, atau payload.
- "apa": satu atau dua kalimat tentang apa yang terjadi.
- "kenapa": satu atau dua kalimat tentang kenapa ini berbahaya bagi markas.
- Jangan menulis langkah tindakan. Langkah sudah ditetapkan SOP di bawah.
- Jangan menambah fakta yang tidak ada di data.
Jawab hanya dengan JSON: {"apa": "...", "kenapa": "..."}

Data kejadian:
- Judul: Perintah asing ke Genset utama
- Dari: Perangkat tak dikenal 10.10.0.66 (jaringan kantor)
- Ke: Genset utama (jaringan peralatan)
...
```

### Permintaan ke Ollama

```json
POST /api/generate
{
  "model": "qwen2.5:1.5b",
  "prompt": "...",
  "stream": false,
  "format": "json",
  "options": {"temperature": 0.2}
}
```

- `stream: false`: jawaban dikirim utuh sekali, tidak sepotong-sepotong.
- `format: "json"`: Ollama memaksa jawaban berbentuk JSON, sehingga mudah dibaca program.
- `temperature: 0.2`: rendah berarti jawaban lebih "tenang" dan konsisten, kurang kreatif. Untuk penjelasan keamanan, itu yang kita mau.

## 5. Pagar pengaman AI

Ini bagian yang paling sering ditanyakan juri. Jawabannya ada di desain:

| Risiko | Pagar di kotak |
|---|---|
| AI mengarang langkah yang berbahaya | AI **tidak boleh** menulis langkah. Langkah selalu dari SOP (`playbook.py`) |
| AI salah memutuskan blokir | AI **tidak punya akses** ke MikroTik. Blokir hanya dari aturan tetap di `detector.py` |
| AI mengarang fakta | Prompt hanya berisi fakta dari sensor, dan AI diminta tidak menambah fakta. Penjelasan bawaan tetap jadi pegangan |
| Jawaban terlalu panjang atau rusak | `_clean` memotong maksimal 420 karakter. Jawaban tanpa `apa` atau `kenapa` ditolak |
| AI mati atau lambat | Penjelasan bawaan tampil sejak detik pertama |
| Diragukan di kemudian hari | Jawaban AI dicatat di catatan bukti (`penjelasan_ai`) beserta nama modelnya |

## Latihan

1. Pasang Ollama di laptopmu, unduh `qwen2.5:1.5b`, lalu jalankan `python -m pjs uji-ai`.
2. Jalankan demo dengan Ollama menyala. Bandingkan penjelasan bawaan dan penjelasan AI untuk kejadian kamera. Mana yang lebih mudah dipahami petugas?
3. Ubah `temperature` menjadi `1.0` di `explainer.py`, jalankan demo dua kali. Apa yang berubah?
4. Coba model lain. Catat waktu jawab dan kualitas bahasa Indonesianya. Tulis hasilnya untuk proposal.

## Kamu paham kalau...

- bisa menjelaskan kenapa AI tidak boleh menentukan blokir dan langkah,
- bisa menjelaskan apa yang terjadi kalau Ollama mati,
- bisa mengganti model dan menguji hasilnya.
