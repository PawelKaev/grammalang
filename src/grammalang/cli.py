"""CLI для GrammaLang."""
import json
import sys
from pathlib import Path
from .pipeline import GrammaPipeline
from .analyzers.rust_analyzer import RustAnalyzer
from .generators.midi_generator import MidiGenerator


class StringSource:
    def __init__(self, text: str) -> None:
        self.text = text

    def load(self) -> str:
        return self.text


def cmd_analyze(text: str, output: str = "output.mid") -> None:
    """Анализирует текст и генерирует MIDI."""
    source = StringSource(text)
    analyzer = RustAnalyzer()
    generator = MidiGenerator()
    pipeline = GrammaPipeline(source, analyzer, generator)

    print(f"[+] Analyzing: {text}")
    midi_bytes = pipeline.run()
    Path(output).write_bytes(midi_bytes)
    print(f"[+] MIDI saved to {output}")


def cmd_prompt_validate(prompt_path: str) -> None:
    """Проверяет промпт на соответствие схеме."""
    data = json.loads(Path(prompt_path).read_text(encoding="utf-8"))
    required = ["id", "version", "template", "output_schema"]
    for field in required:
        if field not in data:
            print(f"[ERROR] Missing field: {field}")
            sys.exit(1)
    print("[+] Prompt is valid.")


def cmd_prompt_run(prompt_path: str, text: str) -> None:
    """Загружает промпт, подставляет текст и выводит результат."""
    prompt = json.loads(Path(prompt_path).read_text(encoding="utf-8"))
    filled = prompt["template"].replace("{text}", text)
    print("[+] Filled prompt:")
    print(filled)
    print("\n[+] Send this to LLM (Ollama/OpenAI).")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="GrammaLang CLI")
    sub = parser.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Analyze text and generate MIDI")
    p_analyze.add_argument("text", help="Text to analyze")
    p_analyze.add_argument("-o", "--output", default="output.mid")

    p_validate = sub.add_parser("prompt-validate", help="Validate a prompt file")
    p_validate.add_argument("path", help="Path to prompt JSON")

    p_run = sub.add_parser("prompt-run", help="Fill a prompt with text")
    p_run.add_argument("path", help="Path to prompt JSON")
    p_run.add_argument("text", help="Text to insert")

    args = parser.parse_args()
    if args.command == "analyze":
        cmd_analyze(args.text, args.output)
    elif args.command == "prompt-validate":
        cmd_prompt_validate(args.path)
    elif args.command == "prompt-run":
        cmd_prompt_run(args.path, args.text)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
