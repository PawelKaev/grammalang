<<<<<<< HEAD
"""
HTTP-сервер для пакетного анализа.
Запуск: python batch_server.py --port 8080
"""

import json
import sys
import tempfile
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from grammalang.batch import BatchAnalyzer


class BatchHandler(BaseHTTPRequestHandler):
    analyzer = BatchAnalyzer(max_workers=4)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._add_cors()
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/batch-analyze':
            self._handle_batch_analyze()
        elif self.path == '/analyze-single':
            self._handle_single_analyze()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self._add_cors()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_batch_analyze(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' in content_type:
                result = self._process_upload()
            else:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                texts = data.get('texts', [])
                if not texts:
                    self._send_error('Нет текстов для анализа')
                    return
                result = self.analyzer.analyze_texts(texts)
            
            self._send_json(self._result_to_dict(result))
        except Exception as e:
            self._send_error(str(e))
    
    def _handle_single_analyze(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            text = data.get('text', '')
            if not text:
                self._send_error('Пустой текст')
                return
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                tmp_path = Path(f.name)
            
            result = self.analyzer.analyze_file(tmp_path)
            tmp_path.unlink()
            
            self._send_json(self._chapter_to_dict(result))
        except Exception as e:
            self._send_error(str(e))
    
    def _process_upload(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        content_type = self.headers.get('Content-Type', '')
        boundary = content_type.split('boundary=')[1].encode()
        parts = body.split(b'--' + boundary)
        
        for part in parts:
            if b'filename=' in part:
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue
                file_content = part[header_end + 4:]
                file_content = file_content.rsplit(b'\r\n', 1)[0]
                
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
                    f.write(file_content)
                    tmp_path = Path(f.name)
                
                result = self.analyzer.analyze_zip(tmp_path)
                tmp_path.unlink()
                return result
        
        raise ValueError('ZIP-файл не найден в запросе')
    
    def _result_to_dict(self, result):
        return {
            'total_chapters': result.total_chapters,
            'success_count': result.success_count,
            'error_count': result.error_count,
            'total_time': result.total_time,
            'timestamp': result.timestamp,
            'total_substances': result.total_substances,
            'total_tensions': result.total_tensions,
            'total_split': result.total_split,
            'total_hold': result.total_hold,
            'total_transition': result.total_transition,
            'total_grammar_change': result.total_grammar_change,
            'chapters': [self._chapter_to_dict(ch) for ch in result.chapters],
            'top_substances': result.top_substances,
            'top_tensions': result.top_tensions,
        }
    
    def _chapter_to_dict(self, ch):
        return {
            'filename': ch.filename,
            'title': ch.title,
            'char_count': ch.char_count,
            'word_count': ch.word_count,
            'sentence_count': ch.sentence_count,
            'substances': ch.substances[:10],
            'tensions': ch.tensions,
            'split_count': ch.split_count,
            'hold_count': ch.hold_count,
            'transition_count': ch.transition_count,
            'grammar_change_count': ch.grammar_change_count,
            'dominant_style': ch.dominant_style,
            'style_confidence': ch.style_confidence,
            'analysis_time': ch.analysis_time,
            'error': ch.error,
        }
    
    def _send_json(self, data):
        self.send_response(200)
        self._add_cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def _send_error(self, message):
        self.send_response(400)
        self._add_cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}, ensure_ascii=False).encode('utf-8'))
    
    def _add_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


def run_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), BatchHandler)
    print(f'[+] Сервер пакетного анализа: http://localhost:{port}')
    print(f'    Health: http://localhost:{port}/health')
    print(f'    Интерфейс: откройте batch.html в браузере')
    print(f'    Ctrl+C для остановки')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[~] Сервер остановлен')
        server.shutdown()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=8080)
    args = parser.parse_args()
    run_server(args.port)
=======
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
    p = argparse.ArgumentParser()
    p.add_argument('--port','-p',type=int,default=8080)
    a = p.parse_args()
    run_server(a.port)
>>>>>>> 3225fb21572d84fa83310be7302ac12b2c5c3a66
