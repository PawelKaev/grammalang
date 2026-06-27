"""HTTP-сервер для пакетного анализа. Запуск: python batch_server.py --port 8080"""
import json, sys, tempfile
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from grammalang.batch import BatchAnalyzer

class BatchHandler(BaseHTTPRequestHandler):
    analyzer = BatchAnalyzer(max_workers=4)

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_POST(self):
        if self.path in ('/batch-analyze', '/analyze-single'): self._handle()
        else: self.send_response(404); self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200); self._cors(); self.end_headers()
            self.wfile.write(json.dumps({'status':'ok'}).encode())
        else: self.send_response(404); self.end_headers()

    def _handle(self):
        try:
            ct = self.headers.get('Content-Type','')
            if 'multipart' in ct: result = self._process_upload()
            else:
                length = int(self.headers.get('Content-Length',0))
                data = json.loads(self.rfile.read(length))
                texts = data.get('texts',[])
                if not texts: raise ValueError('Нет текстов')
                result = self.analyzer.analyze_texts(texts)
            self._send_json(self._result_to_dict(result))
        except Exception as e:
            self.send_response(400); self._cors(); self.end_headers()
            self.wfile.write(json.dumps({'error':str(e)}).encode())

    def _process_upload(self):
        length = int(self.headers.get('Content-Length',0))
        body = self.rfile.read(length)
        ct = self.headers.get('Content-Type','')
        boundary = ct.split('boundary=')[1].encode()
        for part in body.split(b'--'+boundary):
            if b'filename=' in part:
                h_end = part.find(b'\r\n\r\n')
                if h_end == -1: continue
                content = part[h_end+4:].rsplit(b'\r\n',1)[0]
                with tempfile.NamedTemporaryFile(suffix='.zip',delete=False) as f:
                    f.write(content); tp = Path(f.name)
                result = self.analyzer.analyze_zip(tp)
                tp.unlink(); return result
        raise ValueError('ZIP не найден')

    def _result_to_dict(self, r):
        return {
            'total_chapters':r.total_chapters,'success_count':r.success_count,
            'error_count':r.error_count,'total_time':r.total_time,
            'total_substances':r.total_substances,'total_tensions':r.total_tensions,
            'total_split':r.total_split,'total_hold':r.total_hold,
            'total_transition':r.total_transition,'total_grammar_change':r.total_grammar_change,
            'chapters':[self._ch_to_dict(c) for c in r.chapters],
            'top_substances':r.top_substances,'top_tensions':r.top_tensions
        }

    def _ch_to_dict(self, c):
        return {
            'filename':c.filename,'title':c.title,'word_count':c.word_count,
            'substances':c.substances[:10],'tensions':c.tensions,
            'split_count':c.split_count,'hold_count':c.hold_count,
            'transition_count':c.transition_count,'grammar_change_count':c.grammar_change_count,
            'dominant_style':c.dominant_style,'error':c.error
        }

    def _send_json(self, data):
        self.send_response(200); self._cors()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False,indent=2).encode('utf-8'))

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')

def run_server(port=8080):
    s = HTTPServer(('0.0.0.0',port), BatchHandler)
    print(f'[+] Сервер: http://localhost:{port}')
    try: s.serve_forever()
    except KeyboardInterrupt: print('\n[~] Стоп'); s.shutdown()

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--port','-p',type=int,default=8080)
    a = p.parse_args(); run_server(a.port)python batch_server.py --port 8080
