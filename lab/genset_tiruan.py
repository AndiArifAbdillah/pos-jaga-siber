"""Genset tiruan untuk lab: server Modbus TCP kecil + halaman lampu.

Isi "genset":
  coil 0              1 = menyala, 0 = mati
  holding register 0  tegangan (volt)
  holding register 1  frekuensi (Hz)
  holding register 2  bahan bakar (persen)

Fungsi Modbus yang dilayani: 1 (baca coil), 3 (baca register),
5 (tulis satu coil), 15 (tulis banyak coil). Fungsi lain dijawab "tidak dikenal".

Contoh:
  python lab/genset_tiruan.py                      # Modbus di port 5020, lampu di http://localhost:8081
  sudo python3 lab/genset_tiruan.py --port 502     # di VM lab, port Modbus asli
  python lab/genset_tiruan.py --serial COM3        # sekaligus menggerakkan lampu ESP32 (butuh pyserial)
"""

import argparse
import json
import socketserver
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Genset:
    def __init__(self, serial_port=None):
        self.running = True
        self.fuel = 87
        self._lock = threading.Lock()
        self.history = []
        self._serial = None
        if serial_port:
            try:
                import serial  # pyserial
            except ImportError:
                raise SystemExit("Pasang pyserial dulu: pip install pyserial")
            self._serial = serial.Serial(serial_port, 115200, timeout=1)
            time.sleep(2)  # ESP32 menyala ulang saat port dibuka
        self._push_lamp()

    def registers(self):
        with self._lock:
            return [220 if self.running else 0, 50 if self.running else 0, self.fuel]

    def set_running(self, value, who):
        with self._lock:
            changed = value != self.running
            self.running = value
            self.history.insert(0, {"time": time.strftime("%H:%M:%S"), "who": who, "on": value})
            del self.history[20:]
        word = "NYALAKAN" if value else "MATIKAN"
        print(f"{time.strftime('%H:%M:%S')}  {who:>15}  perintah {word}" + ("" if changed else " (tidak berubah)"))
        if changed:
            self._push_lamp()

    def _push_lamp(self):
        if self._serial:
            self._serial.write(b"1\n" if self.running else b"0\n")


def _recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def handle_pdu(genset, pdu, who):
    """Olah satu PDU Modbus, kembalikan PDU balasan."""
    if not pdu:
        return bytes([0x80, 1])
    fc = pdu[0]
    try:
        if fc == 1:  # baca coil
            start, count = struct.unpack(">HH", pdu[1:5])
            bits = [genset.running if start + i == 0 else False for i in range(count)]
            data = bytearray((count + 7) // 8)
            for i, bit in enumerate(bits):
                if bit:
                    data[i // 8] |= 1 << (i % 8)
            return bytes([fc, len(data)]) + bytes(data)
        if fc == 3:  # baca holding register
            start, count = struct.unpack(">HH", pdu[1:5])
            regs = genset.registers()
            values = [regs[start + i] if start + i < len(regs) else 0 for i in range(count)]
            return bytes([fc, count * 2]) + struct.pack(f">{count}H", *values)
        if fc == 5:  # tulis satu coil
            address, value = struct.unpack(">HH", pdu[1:5])
            if address == 0:
                genset.set_running(value == 0xFF00, who)
            return pdu[:5]
        if fc == 15:  # tulis banyak coil
            start, count, _ = struct.unpack(">HHB", pdu[1:6])
            if start == 0 and count >= 1:
                genset.set_running(bool(pdu[6] & 1), who)
            return pdu[:5]
    except (struct.error, IndexError):
        return bytes([fc | 0x80, 3])  # data tidak sah
    return bytes([fc | 0x80, 1])  # fungsi tidak dikenal


def make_modbus_handler(genset):
    class ModbusHandler(socketserver.BaseRequestHandler):
        def handle(self):
            who = self.client_address[0]
            while True:
                header = _recv_exact(self.request, 7)  # MBAP: transaksi, protokol, panjang, unit
                if not header:
                    return
                tid, pid, length, unit = struct.unpack(">HHHB", header)
                pdu = _recv_exact(self.request, length - 1)
                if pdu is None or pid != 0:
                    return
                reply = handle_pdu(genset, pdu, who)
                self.request.sendall(struct.pack(">HHHB", tid, 0, len(reply) + 1, unit) + reply)

    return ModbusHandler


PAGE = """<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Genset tiruan</title>
<style>
body{margin:0;background:#10140e;color:#e6eadf;font:16px system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}
.box{text-align:center;padding:16px}
.lamp{width:180px;height:180px;border-radius:50%;margin:0 auto 18px;background:#2c3527;transition:.3s}
.lamp.on{background:#ffe27a;box-shadow:0 0 80px 20px #ffd54a}
h1{margin:0 0 4px;font-size:22px} .muted{color:#a3ac97;font-size:14px}
button{margin-top:16px;padding:10px 18px;font:inherit;border-radius:6px;border:0;background:#bccc86;color:#1a2010;font-weight:700;cursor:pointer}
ul{list-style:none;padding:0;color:#a3ac97;font-size:13px;font-family:monospace}
</style></head><body><div class="box">
<div class="lamp" id="lamp"></div><h1 id="state">-</h1>
<div class="muted" id="regs">-</div>
<button id="reset" type="button">Nyalakan dari panel</button>
<ul id="hist"></ul></div>
<script>
async function load(){const r=await fetch('/status');const s=await r.json();
document.getElementById('lamp').className='lamp'+(s.running?' on':'');
document.getElementById('state').textContent=s.running?'GENSET MENYALA':'GENSET MATI';
document.getElementById('regs').textContent=s.volt+' V · '+s.hz+' Hz · bahan bakar '+s.fuel+'%';
document.getElementById('hist').innerHTML=s.history.map(h=>'<li>'+h.time+'  '+h.who+'  '+(h.on?'nyalakan':'matikan')+'</li>').join('');}
document.getElementById('reset').onclick=async()=>{await fetch('/nyalakan',{method:'POST'});load();};
load();setInterval(load,700);
</script></body></html>"""


def make_web_handler(genset):
    class WebHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, body, content_type):
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/status":
                volt, hz, fuel = genset.registers()
                return self._send(json.dumps({"running": genset.running, "volt": volt, "hz": hz, "fuel": fuel, "history": genset.history}), "application/json")
            self._send(PAGE, "text/html")

        def do_POST(self):
            if self.path == "/nyalakan":
                genset.set_running(True, "panel genset")
            self._send("{}", "application/json")

    return WebHandler


def main():
    parser = argparse.ArgumentParser(description="Genset tiruan (Modbus TCP) untuk lab Pos Jaga Siber")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5020, help="port Modbus (asli: 502, butuh sudo di Linux)")
    parser.add_argument("--web-port", type=int, default=8081, help="port halaman lampu")
    parser.add_argument("--serial", help="port USB ESP32 lampu, misalnya COM3 atau /dev/ttyUSB0")
    args = parser.parse_args()

    genset = Genset(args.serial)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    modbus = socketserver.ThreadingTCPServer((args.host, args.port), make_modbus_handler(genset))
    modbus.daemon_threads = True
    web = ThreadingHTTPServer((args.host, args.web_port), make_web_handler(genset))
    threading.Thread(target=web.serve_forever, daemon=True).start()
    print(f"Genset tiruan siap. Modbus di port {args.port}, lampu di http://localhost:{args.web_port}")
    try:
        modbus.serve_forever()
    except KeyboardInterrupt:
        print("\nGenset tiruan berhenti.")


if __name__ == "__main__":
    main()
