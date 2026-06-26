import hashlib
from grammalang.pipeline import GrammaPipeline
from grammalang.analyzers.grammar_analyzer import GrammarAnalyzer
from grammalang.generators.midi_generator import MidiGenerator


class StringSource:
    def __init__(self, text: str) -> None:
        self.text = text

    def load(self) -> str:
        return self.text


def test_grammar_analyzer_midi_integration():
    text = (
        "Свобода и необходимость: антиномия чистого разума. "
        "Но разум полагает свободу, однако рассудок мыслит необходимость."
    )
    source = StringSource(text)
    analyzer = GrammarAnalyzer(seed=42)
    generator = MidiGenerator()
    pipeline = GrammaPipeline(source, analyzer, generator)
    midi_bytes = pipeline.run()
    assert len(midi_bytes) > 0

    md5_hash = hashlib.md5(midi_bytes).hexdigest()
    assert md5_hash == "cb2ada83d7f79f129a9b42fb80d26b1b"