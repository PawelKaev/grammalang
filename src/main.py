"""
main.py — точка входа GrammaLang v0.3.
Поддерживает режимы: thought (только онтология), will (только воля), full (оба).
"""

import argparse
import json
import copy
from will_analyzer import WillAnalyzer
from tactical_map import create_tactical_map
from ontological_choice import OntologicalContext, apply_will_to_context, to_d3_json


def main():
    parser = argparse.ArgumentParser(description="GrammaLang v0.3 — анализ мысли и воли")
    parser.add_argument('--input', required=True, help='Путь к входному текстовому файлу')
    parser.add_argument('--output', default='result.json', help='Путь к выходному JSON')
    parser.add_argument('--mode', default='full', choices=['thought', 'will', 'full'],
                        help='Режим: thought (онтология), will (воля), full (оба)')
    parser.add_argument('--plot', action='store_true', help='Сохранить тактическую карту как PNG')
    parser.add_argument('--compare', action='store_true', help='Создать сравнительные графы Парменид/Гераклит')
    args = parser.parse_args()

    # Читаем текст
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    context = OntologicalContext()

    # Анализ воли
    if args.mode in ['will', 'full']:
        print("Анализ воли...")
        will_analyzer = WillAnalyzer()
        indices, sentences = will_analyzer.analyze_text(text)

        context = apply_will_to_context(context, indices, sentences)

        summary = will_analyzer.get_summary(indices)
        print(f"  Средний индекс воли: {summary['mean']:.2f}")
        print(f"  Парменид: {summary['parmenides_share']*100:.0f}% | Гераклит: {summary['heraclitus_share']*100:.0f}% | Нейтрально: {summary['neutral_share']*100:.0f}%")

        if args.plot:
            plot_path = args.output.replace('.json', '_tactical.png')
            json_path = args.output.replace('.json', '_tactical.json')
            create_tactical_map(indices, sentences, plot_path=plot_path, json_path=json_path)
            print(f"  Тактическая карта: {plot_path}")

    # Сравнительные графы
    if args.compare and args.mode in ['will', 'full']:
        print("Создание сравнительных графов...")
        base_context = copy.deepcopy(context)

        parmenides_indices = [1.0] * len(context.will_indices)
        parmenides_ctx = apply_will_to_context(base_context, parmenides_indices, context.sentences)
        with open('parmenides_ontology.json', 'w', encoding='utf-8') as f:
            json.dump(to_d3_json(parmenides_ctx), f, ensure_ascii=False, indent=2)

        heraclitus_indices = [-1.0] * len(context.will_indices)
        heraclitus_ctx = apply_will_to_context(base_context, heraclitus_indices, context.sentences)
        with open('heraclitus_ontology.json', 'w', encoding='utf-8') as f:
            json.dump(to_d3_json(heraclitus_ctx), f, ensure_ascii=False, indent=2)

        print("  parmenides_ontology.json и heraclitus_ontology.json сохранены")

    # Сохраняем результат
    result = context.to_dict()
    result["summary"] = will_analyzer.get_summary(context.will_indices) if context.will_indices else {}

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Результат сохранён в {args.output}")


if __name__ == '__main__':
    main()
