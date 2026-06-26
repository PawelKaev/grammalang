"""HTTP-сервер для визуализатора."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from .analyzers.rust_analyzer import RustAnalyzer


class VisualizerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/analyze":
            content_length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(content_length))
            text = body.get("text", "")

            analyzer = RustAnalyzer()
            ctx = analyzer.analyze(text)

            substances = [
                {"id": s.id, "name": s.name, "energy": s.energy}
                for s in ctx.substances.values()
            ]
            tensions = [
                {"pole_a": t.pole_a, "pole_b": t.pole_b, "status": t.status, "reason": t.reason}
                for t in ctx.tensions
            ]

            response = json.dumps({"substances": substances, "tensions": tensions})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port: int = 8080) -> None:
    server = HTTPServer(("localhost", port), VisualizerHandler)
    print(f"[+] Visualizer server running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Server stopped.")
