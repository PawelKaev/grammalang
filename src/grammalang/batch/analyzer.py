"""
Пакетный анализатор философских глав.
"""
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
    """Агрегированный результат."""
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
        'свобода': 'Свобода', 'необходимость': 'Необходимость', 'разум': 'Разум',
        'рассудок': 'Рассудок', 'чувственность': 'Чувственность',
        'созерцание': 'Созерцание', 'понятие': 'Понятие', 'природа': 'Природа',
        'явление': 'Явление', 'ноумен': 'Ноумен', 'предмет': 'Предмет',
        'субстанция': 'Субстанция', 'причина': 'Причина',
        'пространство': 'Пространство', 'время': 'Время',
        'единство': 'Единство', 'множество': 'Множество',
        'реальность': 'Реальность', 'отрицание': 'Отрицание',
        'возможность': 'Возможность', 'действительность': 'Действительность',
        'мораль': 'Мораль', 'долг': 'Долг', 'воля': 'Воля', 'закон': 'Закон',
        'знание': 'Знание', 'истина': 'Истина', 'бытие': 'Бытие',
        'дух': 'Дух', 'материя': 'Материя', 'сознание': 'Сознание', 'опыт': 'Опыт',
        'априори': 'Априори', 'апостериори': 'Апостериори',
    }

    OPERATOR_MARKERS = {
        'split': ['с одной стороны', 'с другой стороны', 'во-первых', 'во-вторых'],
        'hold': ['антиномия', 'противоречие', 'диалектика', 'но', 'однако', 'хотя'],
        'transition': ['следовательно', 'таким образом', 'далее', 'стало быть'],
        'grammar_change': ['иначе говоря', 'другими словами', 'то есть', 'иными словами'],
    }

    TENSION_PAIRS = [
        ('свобода', 'необходимость', 'антиномия'),
        ('разум', 'чувственность', 'два источника познания'),
        ('созерцание', 'понятие', 'начала познания'),
        ('явление', 'ноумен', 'вещь сама по себе'),
        ('пространство', 'время', 'формы созерцания'),
    ]

    def __init__(self, max_workers=4):
        self.max_workers = max_workers

    def analyze_file(self, filepath):
        """Анализ одного файла."""
        start = time.time()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return ChapterResult(
                filename=str(filepath), error=str(e),
                analysis_time=time.time() - start,
            )

        fp = Path(filepath)
        result = ChapterResult(
            filename=fp.name, char_count=len(text),
            word_count=len(text.split()),
            sentence_count=len([s for s in text.split('.') if s.strip()]),
        )

        lines = text.strip().split('\n')
        result.title = lines[0].strip() if lines else fp.stem

        tl = text.lower()
        sc = {}
        for w, n in self.PHILOSOPHICAL_CATEGORIES.items():
            c = tl.count(w)
            if c > 0:
                sc[w] = {'id': w, 'name': n, 'count': c,
                         'energy': min(1.0, 0.3 + c * 0.05)}

        result.substances = sorted(
            sc.values(), key=lambda x: x['count'], reverse=True
        )[:20]

        fs = set(sc.keys())
        for pa, pb, r in self.TENSION_PAIRS:
            if pa in fs and pb in fs:
                result.tensions.append(
                    {'pole_a': pa, 'pole_b': pb, 'reason': r}
                )

        oc = {'split': 0, 'hold': 0, 'transition': 0, 'grammar_change': 0}
        for ot, ml in self.OPERATOR_MARKERS.items():
            for m in ml:
                oc[ot] += tl.count(m)

        result.split_count = oc['split']
        result.hold_count = oc['hold']
        result.transition_count = oc['transition']
        result.grammar_change_count = oc['grammar_change']

        mo = max(oc, key=oc.get)
        to = sum(oc.values()) or 1
        styles = {'split': 'Структурный', 'hold': 'Диалектический',
                  'transition': 'Переходный', 'grammar_change': 'Рефлексивный'}
        result.dominant_style = styles.get(mo, 'Не определён')
        result.style_confidence = oc[mo] / to
        result.analysis_time = time.time() - start
        return result

    def analyze_directory(self, directory):
        """Анализ директории с .txt файлами."""
        return self._analyze_files(sorted(Path(directory).glob('*.txt')))

    def analyze_files(self, filepaths):
        """Анализ списка файлов."""
        return self._analyze_files([Path(p) for p in filepaths])

    def analyze_zip(self, zip_path):
        """Анализ ZIP-архива."""
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(td)
            return self._analyze_files(sorted(Path(td).glob('**/*.txt')))

    def analyze_texts(self, texts):
        """Анализ текстов из веб-интерфейса."""
        with tempfile.TemporaryDirectory() as td:
            files = []
            for i, item in enumerate(texts):
                fn = item.get('filename', f'chapter_{i+1}.txt')
                ct = item.get('content', '')
                fp = Path(td) / fn
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(ct)
                files.append(fp)
            return self._analyze_files(files)

    def _analyze_files(self, files):
        """Внутренний метод."""
        batch = BatchResult(
            total_chapters=len(files),
            timestamp=datetime.now().isoformat(),
        )
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {ex.submit(self.analyze_file, f): f for f in files}
            for future in as_completed(futures):
                r = future.result()
                batch.chapters.append(r)
                if r.error:
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

        batch.total_time = time.time() - start

        st = {}
        for ch in batch.chapters:
            for s in ch.substances:
                k = s['id']
                if k not in st:
                    st[k] = {'id': k, 'name': s['name'], 'total_count': 0}
                st[k]['total_count'] += s['count']
        batch.top_substances = sorted(
            st.values(), key=lambda x: x['total_count'], reverse=True
        )[:10]

        tt = {}
        for ch in batch.chapters:
            for t in ch.tensions:
                k = f"{t['pole_a']}↔{t['pole_b']}"
                if k not in tt:
                    tt[k] = {**t, 'chapter_count': 0}
                tt[k]['chapter_count'] += 1
        batch.top_tensions = sorted(
            tt.values(), key=lambda x: x['chapter_count'], reverse=True
        )[:10]

        return batch

    def export_csv(self, result, output_path):
        """Экспорт в CSV."""
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Файл', 'Слов', 'Субстанций',
                        'Split', 'Hold', 'Transition', 'GrammarCh',
                        'Стиль', 'Время'])
            for ch in result.chapters:
                w.writerow([
                    ch.filename, ch.word_count, len(ch.substances),
                    ch.split_count, ch.hold_count,
                    ch.transition_count, ch.grammar_change_count,
                    ch.dominant_style, f'{ch.analysis_time:.1f}s',
                ])

    def export_json(self, result, output_path):
        """Экспорт в JSON."""
        def cvt(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: cvt(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [cvt(i) for i in obj]
            return obj
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cvt(result), f, ensure_ascii=False, indent=2)
