"""
GrammaLang Music VM - Прототип 0.1
Генерация философской музыки из онтологических концептов.
"""

import random
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


# -----------------------------------------------------------
# 1. ОНТОЛОГИЧЕСКОЕ ЯДРО
# -----------------------------------------------------------

@dataclass
class Substance:
    """Субстанция — фундаментальная сущность."""
    name: str
    energy: float  # 0.0 - 1.0
    modus: Optional[str] = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Substance) and self.name == other.name


@dataclass
class TensionNode:
    """Узел противоречия между двумя субстанциями."""
    id: str
    pole_a: Substance
    pole_b: Substance
    status: str = "held"  # "held" | "resolved" | "escalated"
    reason: str = ""
    resolved_in_favor_of: Optional[Substance] = None

    def resolve(self, winner: Substance):
        self.status = "resolved"
        self.resolved_in_favor_of = winner

    def escalate(self):
        self.status = "escalated"


@dataclass
class OntologicalContext:
    """
    Контекст Грамматической Машины.
    Содержит карту всех сущностей и противоречий.
    """
    substances: Dict[str, Substance] = field(default_factory=dict)
    tensions: List[TensionNode] = field(default_factory=list)
    boundaries: List[Dict[str, Any]] = field(default_factory=list)

    def add_substance(self, substance: Substance):
        self.substances[substance.name] = substance

    def get_substance(self, name: str) -> Optional[Substance]:
        return self.substances.get(name)

    def create_tension(self, name_a: str, name_b: str, reason: str = "") -> Optional[TensionNode]:
        sub_a = self.get_substance(name_a)
        sub_b = self.get_substance(name_b)
        if not sub_a or not sub_b:
            return None
        node = TensionNode(
            id=f"tension_{len(self.tensions):04d}",
            pole_a=sub_a,
            pole_b=sub_b,
            reason=reason
        )
        self.tensions.append(node)
        return node

    def resolve_tension(self, tension_id: str, winner_name: str) -> bool:
        winner = self.get_substance(winner_name)
        if not winner:
            return False
        for t in self.tensions:
            if t.id == tension_id and t.status == "held":
                t.resolve(winner)
                return True
        return False

    def get_held_tensions(self) -> List[TensionNode]:
        return [t for t in self.tensions if t.status == "held"]

    def get_resolved_tensions(self) -> List[TensionNode]:
        return [t for t in self.tensions if t.status == "resolved"]

    def to_summary(self) -> str:
        lines = ["=== OntologicalContext Summary ==="]
        lines.append(f"Substances: {list(self.substances.keys())}")
        held = self.get_held_tensions()
        resolved = self.get_resolved_tensions()
        lines.append(f"Tensions: {len(self.tensions)} total, {len(held)} held, {len(resolved)} resolved")
        for t in self.tensions:
            lines.append(f"  {t.id}: {t.pole_a.name} vs {t.pole_b.name} [{t.status}]")
        return "\n".join(lines)


# -----------------------------------------------------------
# 2. МУЗЫКАЛЬНЫЙ ГЕНЕРАТОР
# -----------------------------------------------------------

@dataclass
class MusicConfig:
    """Конфигурация музыкальной онтологии."""
    scale: List[int] = field(default_factory=lambda: [60, 62, 64, 65, 67, 69, 71, 72])  # C major
    dissonance_map: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        "antinomy": (60, 66),       # C - F# (тритон)
        "contradiction": (62, 68),  # D - G#
        "opposition": (64, 70),     # E - A#
    })
    resolution_map: Dict[str, List[int]] = field(default_factory=lambda: {
        "freedom": [72, 76, 79],   # C major triad up
        "necessity": [60, 64, 67],  # C major triad down
    })
    tempo: int = 120
    ticks_per_beat: int = 480


@dataclass
class MidiNote:
    pitch: int
    velocity: int
    duration_ticks: int
    position_ticks: int


class MusicGenerator:
    """Генерирует MIDI из OntologicalContext."""

    def __init__(self, config: Optional[MusicConfig] = None):
        self.config = config or MusicConfig()
        random.seed(42)

    def generate(self, context: OntologicalContext, output_path: str) -> str:
        """Генерирует MIDI-файл и возвращает путь к нему."""
        notes = self._context_to_notes(context)
        midi_data = self._notes_to_midi(notes)
        self._save_midi(midi_data, output_path)
        return output_path

    def _context_to_notes(self, context: OntologicalContext) -> List[MidiNote]:
        notes = []
        tick = 0
        tick_step = self.config.ticks_per_beat // 2  # восьмые ноты

        # Субстанции как мелодические линии
        for sub_name, sub in context.substances.items():
            pitch = self._energy_to_pitch(sub.energy)
            velocity = int(64 + sub.energy * 63)  # 64–127
            notes.append(MidiNote(
                pitch=pitch,
                velocity=velocity,
                duration_ticks=tick_step,
                position_ticks=tick
            ))
            tick += tick_step

        # Противоречия как диссонансы
        for tension in context.tensions:
            if tension.status == "held":
                dissonance = self._tension_to_dissonance(tension)
                notes.append(MidiNote(
                    pitch=dissonance[0],
                    velocity=100,
                    duration_ticks=tick_step * 2,
                    position_ticks=tick
                ))
                notes.append(MidiNote(
                    pitch=dissonance[1],
                    velocity=100,
                    duration_ticks=tick_step * 2,
                    position_ticks=tick
                ))
                tick += tick_step * 2
            elif tension.status == "resolved":
                winner = tension.resolved_in_favor_of
                if winner:
                    chord = self._resolution_to_chord(winner.name)
                    for i, p in enumerate(chord):
                        notes.append(MidiNote(
                            pitch=p,
                            velocity=80,
                            duration_ticks=tick_step * 4,
                            position_ticks=tick + i * tick_step
                        ))
                    tick += tick_step * 4

        return notes

    def _energy_to_pitch(self, energy: float) -> int:
        """Отображает энергию субстанции в высоту ноты."""
        scale = self.config.scale
        # energy 0.0 -> низкая нота, 1.0 -> высокая
        idx = int(energy * (len(scale) - 1))
        idx = max(0, min(idx, len(scale) - 1))
        return scale[idx]

    def _tension_to_dissonance(self, tension: TensionNode) -> Tuple[int, int]:
        """Преобразует TensionNode в диссонансный интервал."""
        for keyword, interval in self.config.dissonance_map.items():
            if keyword in tension.reason.lower():
                return interval
        # По умолчанию — тритон
        return (60, 66)

    def _resolution_to_chord(self, substance_name: str) -> List[int]:
        """Возвращает аккорд разрешения для субстанции."""
        name_lower = substance_name.lower()
        for keyword, chord in self.config.resolution_map.items():
            if keyword in name_lower:
                return chord
        # По умолчанию — C major
        return [60, 64, 67]

    def _notes_to_midi(self, notes: List[MidiNote]) -> bytearray:
        """Создаёт MIDI-файл из списка нот."""
        import struct

        midi = bytearray()
        # Header chunk
        midi.extend(b'MThd')
        midi.extend(struct.pack('>I', 6))  # length
        midi.extend(struct.pack('>HHH', 1, 1, self.config.ticks_per_beat))
        # Track chunk
        midi.extend(b'MTrk')
        track_start = len(midi)
        midi.extend(struct.pack('>I', 0))  # placeholder for length

        # Tempo event
        tempo = 60_000_000 // self.config.tempo
        midi.extend(struct.pack('>B', 0x00))  # delta time
        midi.extend(b'\xFF\x51\x03')
        midi.extend(struct.pack('>BH', (tempo >> 16) & 0xFF, tempo & 0xFFFF))

        # Sort notes by position
        events = []
        for note in sorted(notes, key=lambda n: n.position_ticks):
            events.append((note.position_ticks, 'note_on', note.pitch, note.velocity))
            events.append((note.position_ticks + note.duration_ticks, 'note_off', note.pitch, 0))

        events.sort(key=lambda e: e[0])

        last_tick = 0
        for tick, event_type, pitch, velocity in events:
            delta = tick - last_tick
            last_tick = tick
            # Delta time as variable-length quantity
            midi.extend(self._encode_vlq(delta))
            if event_type == 'note_on':
                midi.extend(b'\x90')
                midi.extend(struct.pack('>BB', pitch, velocity))
            else:
                midi.extend(b'\x80')
                midi.extend(struct.pack('>BB', pitch, 0))

        # End of track
        midi.extend(b'\x00\xFF\x2F\x00')

        # Update track length
        track_len = len(midi) - track_start - 4
        struct.pack_into('>I', midi, track_start, track_len)

        return midi

    def _encode_vlq(self, value: int) -> bytes:
        """Кодирует целое как MIDI variable-length quantity."""
        if value == 0:
            return b'\x00'
        result = []
        while value > 0:
            result.insert(0, value & 0x7F)
            value >>= 7
        for i in range(len(result) - 1):
            result[i] |= 0x80
        return bytes(result)

    def _save_midi(self, midi_data: bytearray, output_path: str):
        """Сохраняет MIDI-файл на диск."""
        import os
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(midi_data)
        print(f"[+] MIDI saved to {output_path}")


# -----------------------------------------------------------
# 3. АНАЛИЗАТОР ФИЛОСОФСКИХ ПОНЯТИЙ
# -----------------------------------------------------------

class PhilosophyAnalyzer:
    """
    Анализирует философский текст и строит OntologicalContext.
    """

    def __init__(self):
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

    def analyze(self, text: str) -> OntologicalContext:
        """
        Принимает философский текст, возвращает онтологический контекст.
        """
        context = OntologicalContext()
        text_lower = text.lower()

        # 1. Извлекаем субстанции
        found_substances = []
        for keyword, template in self.substance_templates.items():
            if keyword in text_lower:
                sub = Substance(
                    name=template["name"],
                    energy=template["energy"]
                )
                context.add_substance(sub)
                found_substances.append(sub)

        # Если ничего не найдено — добавляем две субстанции по умолчанию
        if len(found_substances) < 2:
            default_subs = [
                Substance(name="Свобода", energy=0.7),
                Substance(name="Необходимость", energy=0.3),
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
                node = context.create_tension(sub_a.name, sub_b.name, reason)
                if node:
                    # С вероятностью 50% разрешаем противоречие
                    if random.random() < 0.5:
                        winner = sub_a if random.random() < 0.5 else sub_b
                        node.resolve(winner)
                    # С вероятностью 20% эскалируем
                    elif random.random() < 0.2:
                        node.escalate()

        return context

    def _detect_contradiction_type(self, text: str, name_a: str, name_b: str) -> str:
        """Определяет тип противоречия."""
        if "антиномия" in text:
            return "antinomy"
        elif "диалектика" in text:
            return "dialectic"
        elif "оппозиция" in text:
            return "opposition"
        return "contradiction"


# -----------------------------------------------------------
# 4. ТОЧКА ВХОДА И ДЕМОНСТРАЦИЯ
# -----------------------------------------------------------

def main():
    print("=" * 60)
    print("GrammaLang Music VM v0.1")
    print("=" * 60)

    # Тест 1: Свобода и необходимость
    print("\n[Test 1] 'Свобода и необходимость'")
    analyzer = PhilosophyAnalyzer()
    context1 = analyzer.analyze("Свобода и необходимость: антиномия чистого разума")
    print(context1.to_summary())

    generator = MusicGenerator()
    generator.generate(context1, "output/freedom_necessity.mid")

    # Тест 2: Пространство и время
    print("\n[Test 2] 'Пространство и время'")
    context2 = analyzer.analyze("Пространство и время как априорные формы")
    print(context2.to_summary())
    generator.generate(context2, "output/space_time.mid")

    # Тест 3: Единство и множество
    print("\n[Test 3] 'Единство и множество'")
    context3 = analyzer.analyze("Единство и множество в диалектике")
    print(context3.to_summary())
    generator.generate(context3, "output/unity_multiplicity.mid")

    print("\n[+] Все MIDI-файлы сохранены в папку output/")


if __name__ == "__main__":
    main()
