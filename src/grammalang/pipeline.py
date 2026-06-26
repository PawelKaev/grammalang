from __future__ import annotations
from abc import ABC, abstractmethod
from .ontology import OntologicalContext


class MaterialSource(ABC):
    @abstractmethod
    def load(self) -> str:
        ...


class OntologicalAnalyzer(ABC):
    @abstractmethod
    def analyze(self, material: str) -> OntologicalContext:
        ...


class OutputGenerator(ABC):
    @abstractmethod
    def generate(self, context: OntologicalContext) -> bytes:
        ...


class GrammaPipeline:
    def __init__(
        self,
        source: MaterialSource,
        analyzer: OntologicalAnalyzer,
        generator: OutputGenerator,
    ) -> None:
        self.source = source
        self.analyzer = analyzer
        self.generator = generator

    def run(self) -> bytes:
        material = self.source.load()
        context = self.analyzer.analyze(material)
        return self.generator.generate(context)
