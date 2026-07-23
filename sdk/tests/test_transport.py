import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from agentops_local.transport import Transport


class _CaptureHandler(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _CaptureHandler.received.append(json.loads(body))
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):  # silence test server logging
        pass


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_enqueue_posts_payload_in_background():
    _CaptureHandler.received.clear()
    server = HTTPServer(("127.0.0.1", 0), _CaptureHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        transport = Transport(f"http://127.0.0.1:{port}/api/v1/ingest", timeout=2)
        transport.enqueue({"task_name": "t", "model": "m"})
        transport.flush()
        assert _CaptureHandler.received == [{"task_name": "t", "model": "m"}]
        transport.shutdown()
    finally:
        server.shutdown()


def test_backend_down_never_raises():
    # Nothing is listening on this port.
    transport = Transport(f"http://127.0.0.1:{_free_port()}/api/v1/ingest", timeout=1)
    transport.enqueue({"a": 1})
    transport.flush()   # must not raise even though the POST fails
    transport.shutdown()
