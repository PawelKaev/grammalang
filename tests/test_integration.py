import hashlib
from grammalang.pipeline import GrammaPipeline
from grammalang.analyzers.rust_analyzer import RustAnalyzer
from grammalang.generators.midi_generator import MidiGenerator


class StringSource:
    def __init__(self, text: str) -> None:
        self.text = text

    def load(self) -> str:
        return self.text


def test_rust_analyzer_midi_integration():
    source = StringSource("Свобода и необходимость: антиномия чистого разума")
    analyzer = RustAnalyzer()
    generator = MidiGenerator()
    pipeline = GrammaPipeline(source, analyzer, generator)
    midi_bytes = pipeline.run()
    assert len(midi_bytes) > 0
    md5_hash = hashlib.md5(midi_bytes).hexdigest()
    assert md5_hash == "ddcbc82a52b5ef33aea10c590b1c9383"
