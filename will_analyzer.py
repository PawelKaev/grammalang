"""
will_analyzer.py — анализ воли (Парменид vs Гераклит) на уровне предложений.
Использует Rust-ядро для подсчёта маркеров и выполняет постобработку.
"""

import stanza
from typing import List, Tuple
import numpy as np

try:
    import grammalang_core
except ImportError:
    raise ImportError("Не удалось импортировать grammalang_core. Соберите Rust-часть: cd grammalang-core && cargo build")


class WillAnalyzer:
    def __init__(self, language: str = "ru", smoothing_window: int = 3):
        """
        :param language: язык текста (по умолчанию русский)
        :param smoothing_window: размер окна для скользящего среднего (нечётное)
        """
        self.language = language
        self.smoothing_window = smoothing_window if smoothing_window % 2 == 1 else smoothing_window + 1
        self.nlp = stanza.Pipeline(language, processors='tokenize', use_gpu=False)

    def split_sentences(self, text: str) -> List[str]:
        """Разбивает текст на предложения с помощью Stanza."""
        doc = self.nlp(text)
        return [sentence.text for sentence in doc.sentences]

    def analyze_text(self, text: str) -> Tuple[List[float], List[str]]:
        """
        Принимает текст, возвращает список индексов воли и список предложений.
        """
        sentences = self.split_sentences(text)
        if not sentences:
            return [], []

        raw_indices = grammalang_core.analyze_will(sentences)
        smoothed = self._smooth(raw_indices)

        return smoothed, sentences

    def _smooth(self, indices: List[float]) -> List[float]:
        """Сглаживание скользящим средним."""
        if not indices:
            return []
        arr = np.array(indices, dtype=np.float64)
        half = self.smoothing_window // 2
        smoothed = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - half)
            end = min(len(arr), i + half + 1)
            smoothed[i] = np.mean(arr[start:end])
        return smoothed.tolist()

    def get_summary(self, indices: List[float]) -> dict:
        """Сводная статистика по индексам."""
        if not indices:
            return {}
        arr = np.array(indices)
        total = len(arr)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "max": float(np.max(arr)),
            "min": float(np.min(arr)),
            "parmenides_share": float(np.sum(arr > 0.3) / total),
            "heraclitus_share": float(np.sum(arr < -0.3) / total),
            "neutral_share": float(np.sum((arr >= -0.3) & (arr <= 0.3)) / total),
        }


if __name__ == "__main__":
    analyzer = WillAnalyzer()
    test_text = """
    Бытие есть, и оно всегда неизменно. Всё течёт, всё изменяется, но борьба остаётся. 
    Однако мир един в своей основе, и противоположности лишь кажутся.
    """
    indices, sentences = analyzer.analyze_text(test_text)
    for sent, idx in zip(sentences, indices):
        print(f"{sent[:50]:<50} -> {idx:.2f}")
    print("\nСводка:")
    print(analyzer.get_summary(indices))
