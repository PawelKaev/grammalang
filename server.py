import http.server
import socketserver
import json
import sys
import os

PORT = 8080

# Добавляем корень проекта в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from will_analyzer import WillAnalyzer
from ontological_choice import OntologicalChoice, OntologicalContext, to_d3_json


class GrammaHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик запросов для GrammaLang v0.3"""

    # Инициализируем анализатор один раз для всех запросов
    analyzer = None
    chooser = None

    @classmethod
    def init_analyzer(cls):
        if cls.analyzer is None:
            print("Инициализация WillAnalyzer (загрузка Stanza)...")
            cls.analyzer = WillAnalyzer(language="ru", smoothing_window=3)
            cls.chooser = OntologicalChoice(threshold=0.3)
            print("Готово!")

    def do_OPTIONS(self):
        """Обработка preflight CORS-запросов"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Обработка POST-запроса на /analyze"""
        if self.path == '/analyze':
            try:
                # Читаем тело запроса
                content_length = int(self.headers.get('Content-Length', 0))

                if content_length == 0:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    error = json.dumps({"error": "Пустое тело запроса"}, ensure_ascii=False)
                    self.wfile.write(error.encode('utf-8'))
                    return

                post_data = self.rfile.read(content_length)

                if not post_data or len(post_data.strip()) == 0:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    error = json.dumps({"error": "Пустое тело запроса"}, ensure_ascii=False)
                    self.wfile.write(error.encode('utf-8'))
                    return

                data = json.loads(post_data.decode('utf-8'))
                text = data.get('text', '')

                if not text:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    error = json.dumps({"error": "Текст не передан"}, ensure_ascii=False)
                    self.wfile.write(error.encode('utf-8'))
                    return

                # Инициализируем анализатор при первом запросе
                self.init_analyzer()

                # Анализируем текст
                print(f"Анализ текста: {text[:50]}...")
                indices, sentences = self.analyzer.analyze_text(text)
                summary = self.analyzer.get_summary(indices)

                # Создаём контекст с тестовыми субстанциями из текста
                context = OntologicalContext()

                # Извлекаем ключевые слова как субстанции (упрощённо)
                words = text.lower().split()
                word_count = {}
                for word in words:
                    word = word.strip('.,!?:;()-"\'')
                    if len(word) > 3:
                        word_count[word] = word_count.get(word, 0) + 1

                # Топ-5 слов как субстанции
                top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:5]
                for word, count in top_words:
                    context.substances[word] = {"energy": count}

                # Простые модусы
                context.modes = {
                    "пребывает": {"substance": list(context.substances.keys())[0] if context.substances else "", "process": False},
                    "изменяется": {"substance": list(context.substances.keys())[1] if len(context.substances) > 1 else "", "process": True},
                }

                # Онтологический выбор
                context = self.chooser.apply_to_context(context, indices, sentences)

                # Генерируем графы для обеих онтологий
                # Парменид-граф
                parm_context = OntologicalContext()
                parm_context.substances = {}
                for word, count in top_words:
                    parm_context.substances[word] = {"energy": count}
                parm_context.modes = {
                    "пребывает": {"substance": list(parm_context.substances.keys())[0] if parm_context.substances else "", "process": False},
                    "изменяется": {"substance": list(parm_context.substances.keys())[1] if len(parm_context.substances) > 1 else "", "process": True},
                }
                self.chooser._apply_parmenides(parm_context)
                parm_context.ontology_type = 'parmenides'
                parmenides_graph = to_d3_json(parm_context)

                # Гераклит-граф
                hera_context = OntologicalContext()
                hera_context.substances = {}
                for word, count in top_words:
                    hera_context.substances[word] = {"energy": count}
                hera_context.modes = {
                    "пребывает": {"substance": list(hera_context.substances.keys())[0] if hera_context.substances else "", "process": False},
                    "изменяется": {"substance": list(hera_context.substances.keys())[1] if len(hera_context.substances) > 1 else "", "process": True},
                }
                self.chooser._apply_heraclitus(hera_context)
                hera_context.ontology_type = 'heraclitus'
                heraclitus_graph = to_d3_json(hera_context)

                # Формируем ответ
                result = {
                    "indices": indices,
                    "sentences": sentences,
                    "summary": summary,
                    "ontology_type": context.ontology_type,
                    "substances": context.substances,
                    "modes": context.modes,
                    "parmenides_ontology": parmenides_graph,
                    "heraclitus_ontology": heraclitus_graph
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
                print("Ответ отправлен успешно")

            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                error = json.dumps({"error": f"Неверный JSON: {str(e)}"}, ensure_ascii=False)
                self.wfile.write(error.encode('utf-8'))

            except Exception as e:
                print(f"Ошибка при обработке запроса: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                error = json.dumps({"error": str(e)}, ensure_ascii=False)
                self.wfile.write(error.encode('utf-8'))
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


if __name__ == '__main__':
    print(f"GrammaLang v0.3: http://localhost:{PORT}")

    with socketserver.TCPServer(("", PORT), GrammaHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен")
            httpd.shutdown()
