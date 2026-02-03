from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse

_code: Optional[str] = None


class WebserverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _code
        o = urlparse(self.path)
        if not o.path.endswith("/callback"):
            self.send_error(404)
            return
        params = parse_qs(o.query)
        if "code" not in params:
            self.send_error(400)
            return

        _code = params["code"][0]
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Got code, you can close this tab now.")

        thread = Thread(target=self.server.shutdown)
        thread.start()

    def log_request(self, code="-", size="-") -> None:
        pass


def start_code_recv(port: int) -> str:
    print(f"HTTP Server to receive code is listening on http://localhost:{port}")
    server = HTTPServer(("localhost", port), WebserverHandler)
    server.serve_forever()
    assert _code
    return _code
