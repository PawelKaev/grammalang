"""
tactical_map.py — построение тактической карты текста на основе индексов воли.
Визуализация, анализ точек бифуркации, экспорт в JSON.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import json
from typing import List, Tuple, Optional, Dict


class TacticalMap:
    def __init__(self, indices: List[float], sentences: List[str]):
        self.indices = np.array(indices, dtype=np.float64)
        self.sentences = sentences
        self.n = len(indices)
        self.x = np.arange(self.n)

    def find_bifurcation_points(self, threshold: float = 0.3) -> List[int]:
        """Находит индексы предложений со сменой онтологического вектора."""
        if self.n < 2:
            return []
        bifurcations = []
        for i in range(1, self.n):
            prev = self.indices[i-1]
            curr = self.indices[i]
            if prev * curr < 0:
                bifurcations.append(i)
            if abs(prev) < threshold <= abs(curr):
                bifurcations.append(i)
            if abs(curr) < threshold <= abs(prev):
                bifurcations.append(i)
        return list(set(bifurcations))

    def get_zones(self, threshold: float = 0.3) -> Dict[str, List[Tuple[int, int]]]:
        """Возвращает интервалы зон: 'parmenides', 'heraclitus', 'neutral'."""
        zones = {'parmenides': [], 'heraclitus': [], 'neutral': []}
        if self.n == 0:
            return zones
        current_label = None
        start = 0
        for i, val in enumerate(self.indices):
            if val > threshold:
                label = 'parmenides'
            elif val < -threshold:
                label = 'heraclitus'
            else:
                label = 'neutral'
            if current_label is None:
                current_label = label
                start = i
            elif label != current_label:
                zones[current_label].append((start, i-1))
                current_label = label
                start = i
        if current_label is not None:
            zones[current_label].append((start, self.n-1))
        return zones

    def plot(self, output_path: Optional[str] = None,
             figsize: Tuple[int, int] = (12, 6), dpi: int = 100) -> plt.Figure:
        """Строит график тактической карты."""
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.set_xlim(-0.5, self.n - 0.5)
        ax.set_ylim(-1.1, 1.1)
        ax.axhline(0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(0.3, color='red', linestyle=':', linewidth=0.8, alpha=0.4)
        ax.axhline(-0.3, color='blue', linestyle=':', linewidth=0.8, alpha=0.4)

        zones = self.get_zones()
        colors = {'parmenides': 'red', 'heraclitus': 'blue', 'neutral': 'gray'}
        for zone_type, intervals in zones.items():
            color = colors.get(zone_type, 'gray')
            alpha = 0.15 if zone_type != 'neutral' else 0.05
            for start, end in intervals:
                if start <= end:
                    rect = Rectangle((start-0.5, -1.1), end-start+1, 2.2,
                                     facecolor=color, alpha=alpha, edgecolor=None)
                    ax.add_patch(rect)

        ax.plot(self.x, self.indices, marker='o', linestyle='-', color='purple',
                linewidth=2, markersize=6, label='Индекс воли')

        bifurcations = self.find_bifurcation_points()
        if bifurcations:
            ax.scatter(bifurcations, self.indices[bifurcations],
                       color='gold', s=80, zorder=5, label='Точки бифуркации')

        ax.set_xlabel('Номер предложения', fontsize=12)
        ax.set_ylabel('Индекс воли (Парменид → +1, Гераклит → -1)', fontsize=12)
        ax.set_title('Тактическая карта текста', fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=dpi)
            print(f"Тактическая карта сохранена в {output_path}")

        return fig

    def export_json(self, output_path: str) -> None:
        """Экспортирует данные в JSON для веб-визуализатора."""
        data = {
            "sentences": self.sentences,
            "indices": self.indices.tolist(),
            "bifurcations": self.find_bifurcation_points(),
            "zones": self.get_zones(),
            "summary": {
                "mean": float(np.mean(self.indices)),
                "std": float(np.std(self.indices)),
                "max": float(np.max(self.indices)),
                "min": float(np.min(self.indices)),
                "parmenides_share": float(np.sum(self.indices > 0.3) / self.n) if self.n > 0 else 0,
                "heraclitus_share": float(np.sum(self.indices < -0.3) / self.n) if self.n > 0 else 0,
            }
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные тактической карты экспортированы в {output_path}")


def create_tactical_map(indices: List[float], sentences: List[str],
                        plot_path: Optional[str] = None,
                        json_path: Optional[str] = None) -> TacticalMap:
    """Создаёт объект TacticalMap, строит график и экспортирует JSON."""
    tm = TacticalMap(indices, sentences)
    if plot_path:
        tm.plot(output_path=plot_path)
    if json_path:
        tm.export_json(json_path)
    return tm


if __name__ == "__main__":
    test_indices = [0.8, 0.6, -0.2, -0.7, -0.9, -0.3, 0.1, 0.5, 0.7, 0.2, -0.4, -0.6]
    test_sentences = [f"Предложение {i+1}" for i in range(len(test_indices))]
    create_tactical_map(test_indices, test_sentences,
                        plot_path="tactical_map_demo.png",
                        json_path="tactical_map_demo.json")
