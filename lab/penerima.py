"""Penerima di VM "internet palsu": menerima semua sambungan dari skrip kirim_berkala.py.

Contoh:
  sudo python3 lab/penerima.py --port 80
"""

import argparse
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Receiver(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _answer(self):
        length = int(self.headers.get("Content-Length") or 0)
        received = 0
        while received < length:
            chunk = self.rfile.read(min(65536, length - received))
            if not chunk:
                break
            received += len(chunk)
        print(f"{time.strftime('%H:%M:%S')}  dari {self.client_address[0]:<15} {self.command} {received} byte")
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    do_GET = _answer
    do_POST = _answer


def main():
    parser = argparse.ArgumentParser(description="Penerima lalu lintas lab")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=80)
    args = parser.parse_args()
    print(f"Penerima siap di port {args.port}")
    ThreadingHTTPServer((args.host, args.port), Receiver).serve_forever()


if __name__ == "__main__":
    main()
