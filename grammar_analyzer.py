"""GrammarAnalyzer — анализ грамматических структур философского текста."""
import random
from typing import List, Dict, Any
from ..pipeline import OntologicalAnalyzer
from ..ontology import OntologicalContext, Substance, Modus, Boundary, TensionNode


class GrammarAnalyzer(OntologicalAnalyzer):
    """Разбирает текст через NLP, строит онтологический контекст."""

    # Философские категории для поиска в именных группах
    CATEGORIES = {
        "свобода", "необходимость", "пространство", "время",
        "единство", "множество", "субъект", "объект", "дух", "материя",
        "разум", "рассудок", "созерцание", "явление", "вещь", "опыт",
        "причина", "следствие", "субстанция", "акциденция", "форма",
        "содержание", "мышление", "бытие", "ничто", "становление",
        "тезис", "антитезис", "синтез", "идея", "понятие", "категория",
    }

    # Маркеры противоречий
    CONTRAST_MARKERS = {
        "но", "однако", "хотя", "тем не менее", "вопреки",
        "напротив", "с другой стороны", "в то же время",
    }

    # Маркеры отрицания
    NEGATION_MARKERS = {"не", "ни", "без", "вне"}

    def __init__(self, seed: int = 42) -> None:
        random.seed(seed)
        self._nlp = None  # Ленивая загрузка

    @property
    def nlp(self):
        """Загружает stanza один раз."""
        if self._nlp is None:
            import stanza
            try:
                self._nlp = stanza.Pipeline(lang='ru', processors='tokenize,pos,constituency,depparse')
            except Exception:
                stanza.download('ru')
                self._nlp = stanza.Pipeline(lang='ru', processors='tokenize,pos,constituency,depparse')
        return self._nlp

    def analyze(self, material: str) -> OntologicalContext:
        context = OntologicalContext()

        # Разбираем текст через NLP
        doc = self.nlp(material)

        # 1. Извлекаем субстанции
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.upos == "NOUN" and word.lemma in self.CATEGORIES:
                    sub_id = word.lemma
                    if sub_id not in context.substances:
                        # Энергия: чем чаще встречается, тем выше
                        count = sum(1 for s in doc.sentences for w in s.words if w.lemma == word.lemma)
                        energy = min(0.95, 0.3 + count * 0.1)
                        sub = Substance(id=sub_id, name=word.text.capitalize(), energy=energy)
                        context.add_substance(sub)

        # 2. Извлекаем модусы (глаголы-связки и модальные глаголы)
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.upos == "VERB" and word.lemma in {
                    "быть", "являться", "становиться", "полагать",
                    "мыслить", "созерцать", "отрицать", "утверждать",
                }:
                    modus = Modus(name=word.lemma, value=word.text)
                    # Привязываем к первому подлежащему в предложении
                    subj = self._find_subject(sentence)
                    if subj and subj in context.substances:
                        if subj not in context.modi:
                            context.modi[subj] = []
                        context.modi[subj].append(modus)

        # 3. Извлекаем границы (придаточные предложения)
        for sentence in doc.sentences:
            # Упрощённо: если предложение длиннее 10 слов, ставим границу
            if len(sentence.words) > 10:
                boundary = Boundary(
                    name=f"boundary_{len(context.boundaries)}",
                    inside=[w.lemma for w in sentence.words[:5]],
                    outside=[w.lemma for w in sentence.words[5:]],
                )
                context.boundaries.append(boundary)

        # 4. Извлекаем противоречия
        substance_ids = list(context.substances.keys())
        # Ищем маркеры контраста и создаём TensionNode
        for sentence in doc.sentences:
            text_lower = " ".join(w.text.lower() for w in sentence.words)
            for marker in self.CONTRAST_MARKERS:
                if marker in text_lower:
                    # Находим субстанции до и после маркера
                    before, after = text_lower.split(marker, 1)
                    subst_before = [s for s in substance_ids if s in before]
                    subst_after = [s for s in substance_ids if s in after]
                    if subst_before and subst_after:
                        a, b = subst_before[0], subst_after[0]
                        node = context.create_tension(a, b, "contrast")
                        # Разрешаем с вероятностью 40%
                        if node and random.random() < 0.4:
                            context.resolve_tension(node.id, a)

        # Если противоречий не найдено, ищем через отрицания
        if not context.tensions:
            for sentence in doc.sentences:
                words = [w.text.lower() for w in sentence.words]
                for i, w in enumerate(words):
                    if w in self.NEGATION_MARKERS and i + 1 < len(words):
                        negated = sentence.words[i + 1].lemma
                        if negated in substance_ids:
                            # Находим, что утверждается в предложении
                            affirmed = [s for s in substance_ids if s in [x.lemma for x in sentence.words] and s != negated]
                            if affirmed:
                                node = context.create_tension(negated, affirmed[0], "negation")
                                if node and random.random() < 0.6:
                                    context.resolve_tension(node.id, affirmed[0])

        # Если всё ещё нет противоречий — создаём из пар субстанций
        if not context.tensions and len(substance_ids) >= 2:
            for i in range(min(len(substance_ids) - 1, 3)):
                node = context.create_tension(substance_ids[i], substance_ids[i + 1], "copresence")
                if node and random.random() < 0.5:
                    context.resolve_tension(node.id, substance_ids[i])

        return context

    def _find_subject(self, sentence) -> str | None:
        """Находит подлежащее в предложении через дерево зависимостей."""
        for word in sentence.words:
            if word.deprel == "nsubj":
                return word.lemma
        # Запасной вариант: первое существительное в именительном падеже
        for word in sentence.words:
            if word.upos == "NOUN" and "Nom" in (word.feats or ""):
                return word.lemma
        return None
