import random
from ..pipeline import OntologicalAnalyzer
from ..ontology import OntologicalContext, Substance


class KantianAnalyzer(OntologicalAnalyzer):
    def __init__(self) -> None:
        random.seed(42)
        self.substance_templates = {
            "свобода": {"name": "Свобода", "energy": 0.8},
            "необходимость": {"name": "Необходимость", "energy": 0.4},
            "пространство": {"name": "Пространство", "energy": 0.6},
            "время": {"name": "Время", "energy": 0.7},
            "единство": {"name": "Единство", "energy": 0.5},
            "множество": {"name": "Множество", "energy": 0.5},
            "субъект": {"name": "Субъект", "energy": 0.9},
            "объект": {"name": "Объект", "energy": 0.3},
            "дух": {"name": "Дух", "energy": 0.85},
            "материя": {"name": "Материя", "energy": 0.35},
        }

    def analyze(self, material: str) -> OntologicalContext:
        context = OntologicalContext()
        text_lower = material.lower()

        # 1. Извлекаем субстанции
        found_substances = []
        for keyword, template in self.substance_templates.items():
            if keyword in text_lower:
                sub = Substance(
                    id=template["name"].lower(),
                    name=template["name"],
                    energy=template["energy"],
                )
                context.add_substance(sub)
                found_substances.append(sub)

        # Если ничего не найдено — добавляем две субстанции по умолчанию
        if len(found_substances) < 2:
            default_subs = [
                Substance(id="свобода", name="Свобода", energy=0.7),
                Substance(id="необходимость", name="Необходимость", energy=0.3),
            ]
            for sub in default_subs:
                context.add_substance(sub)
                found_substances.append(sub)

        # 2. Создаём противоречия между найденными субстанциями
        for i in range(len(found_substances)):
            for j in range(i + 1, len(found_substances)):
                sub_a = found_substances[i]
                sub_b = found_substances[j]
                reason = self._detect_contradiction_type(text_lower, sub_a.name, sub_b.name)
                node = context.create_tension(sub_a.id, sub_b.id, reason)
                if node:
                    # С вероятностью 50% разрешаем противоречие
                    if random.random() < 0.5:
                        winner = sub_a if random.random() < 0.5 else sub_b
                        context.resolve_tension(node.id, winner.id)
                    # С вероятностью 20% эскалируем
                    elif random.random() < 0.2:
                        # Эскалация — оставляем held с особым статусом
                        pass

        return context

    def _detect_contradiction_type(self, text: str, name_a: str, name_b: str) -> str:
        if "антиномия" in text:
            return "antinomy"
        elif "диалектика" in text:
            return "dialectic"
        elif "оппозиция" in text:
            return "opposition"
        return "contradiction"