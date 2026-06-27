"""
server.py — мини-сервер для GrammaLang v0.3.
Запуск: python server.py
Открыть в браузере: http://localhost:8080
"""

import http.server
import socketserver
import json
import urllib.parse
from will_analyzer import WillAnalyzer
from ontological_choice import OntologicalContext, apply_will_to_context, to_d3_json

PORT = 8080

class GrammaHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/analyze':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            text = data.get('text', '')
            
            # Анализ
            analyzer = WillAnalyzer()
            indices, sentences = analyzer.analyze_text(text)
            
            context = OntologicalContext()
            context.substances = {
                "Бытие": {"energy": 5},
                "Небытие": {"energy": 2},
                "Истина": {"energy": 3},
                "Борьба": {"energy": 4},
                "Поток": {"energy": 3},
            }
            context.modes = {
                "пребывает": {"substance": "Бытие", "type": "static"},
                "изменяется": {"substance": "Поток", "type": "process"},
                "борется": {"substance": "Борьба", "type": "dynamic"},
            }
            context.boundaries = [
                {"from": "Бытие", "to": "Небытие"},
                {"from": "Борьба", "to": "Поток"},
            ]
            
            context = apply_will_to_context(context, indices, sentences)
            summary = analyzer.get_summary(indices)
            
            # Парменид-граф
            import copy
            p_ctx = apply_will_to_context(copy.deepcopy(context), [1.0]*len(indices), sentences)
            h_ctx = apply_will_to_context(copy.deepcopy(context), [-1.0]*len(indices), sentences)
            
            result = {
                'summary': summary,
                'ontology_type': context.ontology_type,
                'indices': indices,
                'sentences': sentences,
                'parmenides_graph': to_d3_json(p_ctx),
                'heraclitus_graph': to_d3_json(h_ctx),
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), GrammaHandler) as httpd:
        print(f"GrammaLang v0.3 запущен: http://localhost:{PORT}")
        httpd.serve_forever()
