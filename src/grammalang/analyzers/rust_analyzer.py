import json
import sys
from pathlib import Path

_bridge_dir = Path(__file__).parent.parent / "rust_bridge"
if str(_bridge_dir) not in sys.path:
    sys.path.insert(0, str(_bridge_dir))

from ..pipeline import OntologicalAnalyzer
from ..ontology import OntologicalContext


class RustAnalyzer(OntologicalAnalyzer):
    def analyze(self, material: str) -> OntologicalContext:
        import grammalang_core

        json_str = grammalang_core.analyze_text(material)
        data = json.loads(json_str)
        return OntologicalContext.from_dict(data)
