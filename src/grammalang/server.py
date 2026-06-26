"""HTTP-сервер для визуализатора GrammaLang."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from .analyzers.grammar_analyzer import GrammarAnalyzer


class VisualizerHandler(BaseHTTPRequestHandler):
    analyzer = None

    @classmethod
    def get_analyzer(cls):
        if cls.analyzer is None:
            cls.analyzer = GrammarAnalyzer(seed=42)
        return cls.analyzer

    def do_POST(self):
        if self.path == "/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))
            text = body.get("text", "")

            analyzer = self.get_analyzer()
            ctx = analyzer.analyze(text)

            substances = []
            for s in ctx.substances.values():
                modi = ctx.modi.get(s.id, [])
                substances.append({
                    "id": s.id,
                    "name": s.name,
                    "energy": s.energy,
                    "modi": [{"name": m.name, "value": m.value} for m in modi]
                })

            tensions = []
            for t in ctx.tensions:
                tensions.append({
                    "id": t.id,
                    "pole_a": t.pole_a,
                    "pole_b": t.pole_b,
                    "status": t.status,
                    "reason": t.reason
                })

            boundaries = []
            for b in ctx.boundaries:
                boundaries.append({
                    "name": b.name,
                    "inside": b.inside,
                    "outside": b.outside
                })

            result = {
                "substances": substances,
                "tensions": tensions,
                "boundaries": boundaries,
                "stats": {
                    "total_substances": len(substances),
                    "total_tensions": len(tensions),
                    "held_tensions": sum(1 for t in tensions if t["status"] == "held"),
                    "resolved_tensions": sum(1 for t in tensions if t["status"] == "resolved"),
                }
            }

            response = json.dumps(result, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
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
    print(f"[+] GrammaLang Visualizer server at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Server stopped.")
