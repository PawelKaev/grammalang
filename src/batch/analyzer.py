"""
Пакетный анализатор философских глав.
Использование:
    from grammalang.batch import BatchAnalyzer
    
    analyzer = BatchAnalyzer(max_workers=4)
    result = analyzer.analyze_directory(Path('./chapters/'))
    analyzer.export_csv(result, Path('results.csv'))
"""

import os
import json
import csv
import time
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ChapterResult:
    """Результат анализа одной главы."""
    filename: str
    title: str = ""
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    substances: List[Dict] = field(default_factory=list)
    tensions: List[Dict] = field(default_factory=list)
    split_count: int = 0
    hold_count: int = 0
    transition_count: int = 0
    grammar_change_count: int = 0
    dominant_style: str = ""
    style_confidence: float = 0.0
    analysis_time: float = 0.0
    error: Optional[str] = None


@dataclass
class BatchResult:
    """Агрегированный результат пакетного анализа."""
    total_chapters: int = 0
    success_count: int = 0
    error_count: int = 0
    total_time: float = 0.0
    timestamp: str = ""
    total_substances: int = 0
    total_tensions: int = 0
    total_split: int = 0
    total_hold: int = 0
    total_transition: int = 0
    total_grammar_change: int = 0
    chapters: List[ChapterResult] = field(default_factory=list)
    top_substances: List[Dict] = field(default_factory=list)
    top_tensions: List[Dict] = field(default_factory=list)


class BatchAnalyzer:
    """Пакетный анализатор философских текстов."""
    
    PHILOSOPHICAL_CATEGORIES = {
        'разум': 'Разум', 'рассудок': 'Рассудок', 'чувственность': 'Чувственность',
        'созерцание': 'Созерцание', 'понятие': 'Понятие', 'природа': 'Природа',
        'свобода': 'Свобода', 'необходимость': 'Необходимость', 'явление': 'Явление',
        'феномен': 'Феномен', 'ноумен': 'Ноумен', 'предмет': 'Предмет',
        'субстанция': 'Субстанция', 'причина': 'Причина', 'следствие': 'Следствие',
        'пространство': 'Пространство', 'время': 'Время', 'единство': 'Единство',
        'множество': 'Множество', 'реальность': 'Реальность', 'отрицание': 'Отрицание',
        'возможность': 'Возможность', 'действительность': 'Действительность',
        'мораль': 'Мораль', 'долг': 'Долг', 'воля': 'Воля', 'закон': 'Закон',
        'знание': 'Знание', 'истина': 'Истина', 'бытие': 'Бытие', 'дух': 'Дух',
        'материя': 'Материя', 'сознание': 'Сознание', 'опыт': 'Опыт',
        'априори': 'Априори', 'апостериори': 'Апостериори',
        'трансцендентальный': 'Трансцендентальное',
    }
    
    OPERATOR_MARKERS = {
        'split': [
            'с одной стороны', 'с другой стороны', 'во-первых', 'во-вторых',
            'в-третьих', 'прежде всего', 'затем', 'наконец', 'разделим', 'различать',
        ],
        'hold': [
            'антиномия', 'противоречие', 'противоположность', 'диалектика', 'парадокс',
            'но', 'однако', 'тем не менее', 'хотя', 'вопреки',
        ],
        'transition': [
            'следовательно', 'таким образом', 'далее', 'перейдём', 'стало быть',
            'в свою очередь', 'напротив', 'наоборот', 'итак', 'отсюда следует',
        ],
        'grammar_change': [
            'иначе говоря', 'другими словами', 'то есть', 'а именно', 'иными словами',
            'в сущности', 'по сути', 'строго говоря', 'собственно', 'в строгом смысле',
        ],
    }
    
    TENSION_PAIRS = [
        ('разум', 'чувственность', 'два источника познания'),
        ('созерцание', 'понятие', 'начала познания'),
        ('свобода', 'необходимость', 'антиномия'),
        ('явление', 'ноумен', 'вещь сама по себе'),
        ('пространство', 'время', 'формы созерцания'),
        ('дух', 'материя', 'основной вопрос философии'),
        ('бытие', 'сознание', 'онтологический вопрос'),
        ('априори', 'апостериори', 'источники знания'),
        ('единство', 'множество', 'категории количества'),
        ('возможность', 'действительность', 'категории модальности'),
    ]
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def analyze_file(self, filepath: Path) -> ChapterResult:
        """Анализ одного файла."""
        start_time = time.time()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return ChapterResult(
                filename=filepath.name,
                error=str(e),
                analysis_time=time.time() - start_time,
            )
        
        result = ChapterResult(
            filename=filepath.name,
            char_count=len(text),
            word_count=len(text.split()),
            sentence_count=len([s for s in text.split('.') if s.strip()]),
        )
        
        lines = text.strip().split('\n')
        result.title = lines[0].strip() if lines else filepath.stem
        
        text_lower = text.lower()
        substance_counts = {}
        
        for word, name in self.PHILOSOPHICAL_CATEGORIES.items():
            count = text_lower.count(word)
            if count > 0:
                substance_counts[word] = {
                    'id': word, 'name': name, 'count': count,
                    'energy': min(1.0, 0.3 + count * 0.05),
                }
        
        result.substances = sorted(
            substance_counts.values(), key=lambda x: x['count'], reverse=True
        )[:20]
        
        found_substances = set(substance_counts.keys())
        for pole_a, pole_b, reason in self.TENSION_PAIRS:
            if pole_a in found_substances and pole_b in found_substances:
                result.tensions.append({
                    'pole_a': pole_a, 'pole_b': pole_b, 'reason': reason,
                })
        
        op_counts = {'split': 0, 'hold': 0, 'transition': 0, 'grammar_change': 0}
        for op_type, markers in self.OPERATOR_MARKERS.items():
            for marker in markers:
                op_counts[op_type] += text_lower.count(marker)
        
        result.split_count = op_counts['split']
        result.hold_count = op_counts['hold']
        result.transition_count = op_counts['transition']
        result.grammar_change_count = op_counts['grammar_change']
        
        max_op = max(op_counts, key=op_counts.get)
        total_ops = sum(op_counts.values()) or 1
        
        styles = {
            'split': 'Структурный / аналитический',
            'hold': 'Диалектический / проблематизирующий',
            'transition': 'Переходный / синтезирующий',
            'grammar_change': 'Рефлексивный / мета-уровневый',
        }
        
        result.dominant_style = styles.get(max_op, 'Не определён')
        result.style_confidence = op_counts[max_op] / total_ops
        result.analysis_time = time.time() - start_time
        
        return result
    
    def analyze_directory(self, directory: Path) -> BatchResult:
        """Анализ всех .txt файлов в директории."""
        files = sorted(directory.glob('*.txt'))
        return self._analyze_files(files)
    
    def analyze_files(self, filepaths: List[Path]) -> BatchResult:
        """Анализ списка файлов."""
        return self._analyze_files(filepaths)
    
    def analyze_zip(self, zip_path: Path) -> BatchResult:
        """Анализ глав из ZIP-архива."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir)
            files = sorted(Path(tmpdir).glob('**/*.txt'))
            return self._analyze_files(files)
    
    def analyze_texts(self, texts: List[Dict]) -> BatchResult:
        """Анализ списка текстов (из веб-интерфейса)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = []
            for i, item in enumerate(texts):
                filename = item.get('filename', f'chapter_{i+1}.txt')
                content = item.get('content', '')
                filepath = Path(tmpdir) / filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                files.append(filepath)
            return self._analyze_files(files)
    
    def _analyze_files(self, files: List[Path]) -> BatchResult:
        """Внутренний метод анализа списка файлов."""
        batch = BatchResult(
            total_chapters=len(files),
            timestamp=datetime.now().isoformat(),
        )
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.analyze_file, f): f for f in files}
            for future in as_completed(futures):
                result = future.result()
                batch.chapters.append(result)
                if result.error:
                    batch.error_count += 1
                else:
                    batch.success_count += 1
        
        batch.chapters.sort(key=lambda c: c.filename)
        
        for ch in batch.chapters:
            if ch.error:
                continue
            batch.total_substances += len(ch.substances)
            batch.total_tensions += len(ch.tensions)
            batch.total_split += ch.split_count
            batch.total_hold += ch.hold_count
            batch.total_transition += ch.transition_count
            batch.total_grammar_change += ch.grammar_change_count
        
        batch.total_time = time.time() - start_time
        
        substance_totals = {}
        for ch in batch.chapters:
            for sub in ch.substances:
                key = sub['id']
                if key not in substance_totals:
                    substance_totals[key] = {'id': key, 'name': sub['name'], 'total_count': 0}
                substance_totals[key]['total_count'] += sub['count']
        
        batch.top_substances = sorted(
            substance_totals.values(), key=lambda x: x['total_count'], reverse=True
        )[:10]
        
        tension_totals = {}
        for ch in batch.chapters:
            for t in ch.tensions:
                key = f"{t['pole_a']}↔{t['pole_b']}"
                if key not in tension_totals:
                    tension_totals[key] = {**t, 'chapter_count': 0}
                tension_totals[key]['chapter_count'] += 1
        
        batch.top_tensions = sorted(
            tension_totals.values(), key=lambda x: x['chapter_count'], reverse=True
        )[:10]
        
        return batch
    
    def export_csv(self, result: BatchResult, output_path: Path):
        """Экспорт результатов в CSV."""
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Файл', 'Заголовок', 'Символов', 'Слов', 'Предложений',
                'Субстанций', 'Противоречий',
                'Split', 'Hold', 'Transition', 'Grammar Change',
                'Доминирующий стиль', 'Уверенность', 'Время анализа', 'Ошибка',
            ])
            for ch in result.chapters:
                writer.writerow([
                    ch.filename, ch.title, ch.char_count, ch.word_count,
                    ch.sentence_count, len(ch.substances), len(ch.tensions),
                    ch.split_count, ch.hold_count, ch.transition_count,
                    ch.grammar_change_count, ch.dominant_style,
                    f"{ch.style_confidence:.2f}", f"{ch.analysis_time:.2f}s",
                    ch.error or '',
                ])
    
    def export_json(self, result: BatchResult, output_path: Path):
        """Экспорт результатов в JSON."""
        def convert(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: convert(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            return obj
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(convert(result), f, ensure_ascii=False, indent=2)
