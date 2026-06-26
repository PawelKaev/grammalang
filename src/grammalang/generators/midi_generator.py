import io
import struct
import random
from typing import List, Tuple
from ..pipeline import OutputGenerator
from ..ontology import OntologicalContext


class MidiGenerator(OutputGenerator):
    def __init__(self) -> None:
        random.seed(42)
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C major
        self.tempo = 120
        self.ticks_per_beat = 480
        self.dissonance_map = {
            "antinomy": (60, 66),
            "contradiction": (62, 68),
            "opposition": (64, 70),
        }
        self.resolution_map = {
            "свобода": [72, 76, 79],
            "необходимость": [60, 64, 67],
        }

    def generate(self, context: OntologicalContext) -> bytes:
        notes = self._context_to_notes(context)
        midi_data = self._notes_to_midi(notes)
        buf = io.BytesIO()
        buf.write(midi_data)
        return buf.getvalue()

    def _context_to_notes(self, context: OntologicalContext) -> List["MidiNote"]:
        notes = []
        tick = 0
        tick_step = self.ticks_per_beat // 2  # восьмые ноты

        for sub_id, sub in context.substances.items():
            pitch = self._energy_to_pitch(sub.energy)
            velocity = int(64 + sub.energy * 63)
            notes.append(MidiNote(
                pitch=pitch,
                velocity=velocity,
                duration_ticks=tick_step,
                position_ticks=tick,
            ))
            tick += tick_step

        for tension in context.tensions:
            if tension.status == "held":
                dissonance = self._tension_to_dissonance(tension)
                notes.append(MidiNote(
                    pitch=dissonance[0],
                    velocity=100,
                    duration_ticks=tick_step * 2,
                    position_ticks=tick,
                ))
                notes.append(MidiNote(
                    pitch=dissonance[1],
                    velocity=100,
                    duration_ticks=tick_step * 2,
                    position_ticks=tick,
                ))
                tick += tick_step * 2
            elif tension.status == "resolved":
                # Находим победителя
                winner_id = tension.resolved_at_utc  # заглушка, у нас нет winner_id в TensionNode
                # Ищем субстанцию с подходящим именем
                chord = None
                for keyword, c in self.resolution_map.items():
                    if keyword in tension.pole_a or keyword in tension.pole_b:
                        chord = c
                        break
                if chord is None:
                    chord = [60, 64, 67]
                for i, p in enumerate(chord):
                    notes.append(MidiNote(
                        pitch=p,
                        velocity=80,
                        duration_ticks=tick_step * 4,
                        position_ticks=tick + i * tick_step,
                    ))
                tick += tick_step * 4

        return notes

    def _energy_to_pitch(self, energy: float) -> int:
        idx = int(energy * (len(self.scale) - 1))
        idx = max(0, min(idx, len(self.scale) - 1))
        return self.scale[idx]

    def _tension_to_dissonance(self, tension) -> Tuple[int, int]:
        for keyword, interval in self.dissonance_map.items():
            if keyword in tension.reason.lower():
                return interval
        return (60, 66)

    def _notes_to_midi(self, notes: List["MidiNote"]) -> bytearray:
        midi = bytearray()
        midi.extend(b'MThd')
        midi.extend(struct.pack('>I', 6))
        midi.extend(struct.pack('>HHH', 1, 1, self.ticks_per_beat))
        midi.extend(b'MTrk')
        track_start = len(midi)
        midi.extend(struct.pack('>I', 0))

        tempo = 60_000_000 // self.tempo
        midi.extend(struct.pack('>B', 0x00))
        midi.extend(b'\xFF\x51\x03')
        midi.extend(struct.pack('>BH', (tempo >> 16) & 0xFF, tempo & 0xFFFF))

        events = []
        for note in sorted(notes, key=lambda n: n.position_ticks):
            events.append((note.position_ticks, 'note_on', note.pitch, note.velocity))
            events.append((note.position_ticks + note.duration_ticks, 'note_off', note.pitch, 0))

        events.sort(key=lambda e: e[0])

        last_tick = 0
        for tick, event_type, pitch, velocity in events:
            delta = tick - last_tick
            last_tick = tick
            midi.extend(self._encode_vlq(delta))
            if event_type == 'note_on':
                midi.extend(b'\x90')
                midi.extend(struct.pack('>BB', pitch, velocity))
            else:
                midi.extend(b'\x80')
                midi.extend(struct.pack('>BB', pitch, 0))

        midi.extend(b'\x00\xFF\x2F\x00')
        track_len = len(midi) - track_start - 4
        struct.pack_into('>I', midi, track_start, track_len)

        return midi

    def _encode_vlq(self, value: int) -> bytes:
        if value == 0:
            return b'\x00'
        result = []
        while value > 0:
            result.insert(0, value & 0x7F)
            value >>= 7
        for i in range(len(result) - 1):
            result[i] |= 0x80
        return bytes(result)


class MidiNote:
    def __init__(self, pitch: int, velocity: int, duration_ticks: int, position_ticks: int):
        self.pitch = pitch
        self.velocity = velocity
        self.duration_ticks = duration_ticks
        self.position_ticks = position_ticks
