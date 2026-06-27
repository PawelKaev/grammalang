"""
ontological_choice.py — выбор типа онтологии на основе индекса воли.
Модифицирует структуру OntologicalContext (субстанции, модусы, границы).
"""

import copy
import numpy as np
from typing import List, Dict, Any


class OntologicalContext:
    """Контекст онтологии."""
    def __init__(self):
        self.substances = {}
        self.modes = {}
        self.boundaries = []
        self.ontology_type = "hybrid"
        self.will_indices = []
        self.sentences = []
        self.relations = []

    def to_dict(self):
        return {
            "substances": self.substances,
            "modes": self.modes,
            "boundaries": self.boundaries,
            "ontology_type": self.ontology_type,
            "will_indices": self.will_indices,
            "sentences": self.sentences,
        }


class OntologicalChoice:
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self._original_substances = {}  # сохраняем оригинал

    def choose_ontology_type(self, indices: List[float]) -> str:
        if not indices:
            return 'hybrid'
        mean_idx = np.mean(indices)
        if mean_idx > self.threshold:
            return 'parmenides'
        elif mean_idx < -self.threshold:
            return 'heraclitus'
        else:
            return 'hybrid'

    def apply_to_context(self, context: 'OntologicalContext',
                          indices: List[float],
                          sentences: List[str]) -> 'OntologicalContext':
        new_context = copy.deepcopy(context)
        new_context.ontology_type = self.choose_ontology_type(indices)
        new_context.will_indices = indices
        new_context.sentences = sentences

        # Сохраняем оригинальные субстанции до изменения
        self._original_substances = copy.deepcopy(context.substances)

        if new_context.ontology_type == 'parmenides':
            self._apply_parmenides(new_context)
        elif new_context.ontology_type == 'heraclitus':
            self._apply_heraclitus(new_context)
        else:
            self._apply_hybrid(new_context)

        return new_context

    def _apply_parmenides(self, context: 'OntologicalContext'):
        """Иерархия: одна главная субстанция, остальные удаляются."""
        if not context.substances:
            return
        # Находим субстанцию с максимальной энергией
        main_sub = max(context.substances.items(), key=lambda x: x[1].get('energy', 0))
        main_name = main_sub[0]
        main_data = main_sub[1]
        # Оставляем только главную
        context.substances = {main_name: main_data}
        # Все модусы привязываем к главной
        for name, mode in context.modes.items():
            mode['substance'] = main_name
            mode['process'] = False
        # Границы удаляем (в Едином нет границ)
        context.boundaries = []

    def _apply_heraclitus(self, context: 'OntologicalContext'):
        """Сеть: все субстанции сохраняются, уравниваются, процессуальность."""
        # Восстанавливаем все оригинальные субстанции, если они были удалены
        if self._original_substances:
            context.substances = copy.deepcopy(self._original_substances)
        # Уравниваем энергию
        for sub in context.substances.values():
            sub['energy'] = 1.0
        # Все модусы — процессы
        for mode in context.modes.values():
            mode['process'] = True
        # Границы делаем проницаемыми
        for boundary in context.boundaries:
            boundary['rigid'] = False
            boundary['permeable'] = True

    def _apply_hybrid(self, context: 'OntologicalContext'):
        """Гибрид: без изменений."""
        context.ontology_type = 'hybrid'


def apply_will_to_context(context: 'OntologicalContext',
                          indices: List[float],
                          sentences: List[str],
                          threshold: float = 0.3) -> 'OntologicalContext':
    chooser = OntologicalChoice(threshold)
    return chooser.apply_to_context(context, indices, sentences)


def to_d3_json(context: 'OntologicalContext') -> Dict[str, List[Dict]]:
    """Преобразует контекст в формат для D3.js."""
    nodes = []
    links = []
    node_set = set()

    for sub_name, sub_data in context.substances.items():
        nodes.append({
            "id": sub_name,
            "type": "substance",
            "energy": sub_data.get("energy", 1.0)
        })
        node_set.add(sub_name)

    for mode_name, mode_data in context.modes.items():
        if mode_name not in node_set:
            nodes.append({
                "id": mode_name,
                "type": "mode",
                "process": mode_data.get("process", False)
            })
            node_set.add(mode_name)
        if "substance" in mode_data and mode_data["substance"] in node_set:
            links.append({
                "source": mode_name,
                "target": mode_data["substance"],
                "type": "mode_relation"
            })

    for boundary in context.boundaries:
        if "from" in boundary and "to" in boundary:
            if boundary["from"] in node_set and boundary["to"] in node_set:
                links.append({
                    "source": boundary["from"],
                    "target": boundary["to"],
                    "type": "boundary",
                    "rigid": boundary.get("rigid", False)
                })

    return {"nodes": nodes, "links": links}
