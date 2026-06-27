"""
main.py — точка входа GrammaLang v0.3.
"""

import argparse
import json
import copy
from will_analyzer import WillAnalyzer
from tactical_map import create_tactical_map
from ontological_choice import OntologicalContext, apply_will_to_context, to_d3_json


def main():
    parser = argparse.ArgumentParser(description="GrammaLang v0.3")
    parser.add_argument('--input', required=True, help='Путь к входному файлу')
    parser.add_argument('--output', default='result.json', help='Путь к выходному JSON')
    parser.add_argument('--mode', default='full', choices=['thought', 'will', 'full'])
    parser.add_argument('--plot', action='store_true', help='Сохранить график')
    parser.add_argument('--compare', action='store_true', help='Сравнительные графы')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    context = OntologicalContext()
    # Тестовые субстанции для демонстрации графов
    context.substances = {
        "Бытие": {"energy": 5},
        "Небытие": {"energy": 2},
        "Истина": {"energy": 3},
        "Борьба": {"energy": 4},
        "Поток": {"energy": 3},
    }
    context.modes = {
        "пребывает": {"substance": "Бытие", "type": "static"},
        "изменяется": {"substance": "Поток", "type": "process"},
        "борется": {"substance": "Борьба", "type": "dynamic"},
    }
    context.boundaries = [
        {"from": "Бытие", "to": "Небытие"},
        {"from": "Борьба", "to": "Поток"},
    ]

    if args.mode in ['will', 'full']:
        print("Анализ воли...")
        will_analyzer = WillAnalyzer()
        indices, sentences = will_analyzer.analyze_text(text)
        context = apply_will_to_context(context, indices, sentences)
        summary = will_analyzer.get_summary(indices)
        print(f"  Средний индекс: {summary['mean']:.2f}")
        print(f"  Парменид: {summary['parmenides_share']*100:.0f}% | Гераклит: {summary['heraclitus_share']*100:.0f}%")

        if args.plot:
            plot_path = args.output.replace('.json', '_tactical.png')
            json_path = args.output.replace('.json', '_tactical.json')
            create_tactical_map(indices, sentences, plot_path=plot_path, json_path=json_path)
            print(f"  График сохранён: {plot_path}")

    if args.compare:
        base = copy.deepcopy(context)
        p_ctx = apply_will_to_context(base, [1.0]*len(context.will_indices), context.sentences)
        with open('parmenides_ontology.json', 'w', encoding='utf-8') as f:
            json.dump(to_d3_json(p_ctx), f, ensure_ascii=False, indent=2)
        h_ctx = apply_will_to_context(base, [-1.0]*len(context.will_indices), context.sentences)
        with open('heraclitus_ontology.json', 'w', encoding='utf-8') as f:
            json.dump(to_d3_json(h_ctx), f, ensure_ascii=False, indent=2)
        print("  Сравнительные графы сохранены")

    result = context.to_dict()
    result["summary"] = will_analyzer.get_summary(context.will_indices) if context.will_indices else {}
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Результат: {args.output}")


if __name__ == '__main__':
    main()
