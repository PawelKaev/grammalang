// will_markers.rs — модуль для анализа воли (Парменид vs Гераклит)

/// Парменид: воля к единству, неподвижности, категоричности, императивности
const PARMENIDES_MARKERS: &[&str] = &[
    // Связки жёсткого тождества
    "есть", "суть", "является", "тождественно", "равно", "идентично",
    // Абсолютные наречия
    "всегда", "никогда", "вечно", "неизменно", "абсолютно",
    "безусловно", "непременно", "всецело", "целиком", "полностью",
    // Императивы и долженствование
    "должен", "обязан", "необходимо", "надо", "нужно",
    // Категоричность
    "определённо", "именно", "истинно", "единственно", "только",
    "исключительно", "однозначно",
    // Единство и неподвижность
    "сущее", "бытие", "единое", "неподвижное", "вечное",
    "неизменное", "целое", "закон",
];

/// Гераклит: воля к процессу, изменению, множественности, диалогу
const HERACLITUS_MARKERS: &[&str] = &[
    // Процессуальные глаголы
    "изменяется", "меняется", "превращается", "переходит",
    "течёт", "движется", "развивается", "становление",
    // Множественность
    "множество", "многообразие", "различие", "разнообразие",
    // Противоречие и борьба
    "противоречие", "борьба", "война", "конфликт",
    "противоположность", "напряжение", "столкновение",
    // Текучесть и непостоянство
    "текучесть", "изменчивость", "непостоянно", "относительно",
    "течение", "поток", "волна",
    // Диалогичность и оговорки
    "однако", "впрочем", "зато", "хотя",
    "возможно", "вероятно", "иногда", "отчасти",
    "может", "может быть", "способен",
    // С одной стороны... с другой
    "стороны",
];

pub fn analyze_sentence(sentence: &str) -> (usize, usize, usize) {
    let lower = sentence.to_lowercase();
    let words: Vec<&str> = lower
        .split_whitespace()
        .map(|w| w.trim_matches(|c: char| !c.is_alphanumeric() && c != '-'))
        .filter(|w| !w.is_empty())
        .collect();

    let total_words: usize = words.len();
    let mut parmenides: usize = 0;
    let mut heraclitus: usize = 0;

    for word in &words {
        if PARMENIDES_MARKERS.contains(word) {
            parmenides += 1;
        }
        if HERACLITUS_MARKERS.contains(word) {
            heraclitus += 1;
        }
    }

    // Учёт отрицаний: "не есть", "ни один" и т.д.
    let mut negated_parmenides: usize = 0;
    let mut negated_heraclitus: usize = 0;
    for i in 0..words.len() {
        let word = words[i];
        if word == "не" || word == "ни" || word == "нет" {
            if i + 1 < words.len() {
                let next = words[i + 1];
                if PARMENIDES_MARKERS.contains(&next) {
                    negated_parmenides += 1;
                }
                if HERACLITUS_MARKERS.contains(&next) {
                    negated_heraclitus += 1;
                }
            }
        }
    }

    (
        parmenides.saturating_sub(negated_parmenides),
        heraclitus.saturating_sub(negated_heraclitus),
        total_words,
    )
}

pub fn will_index(sentence: &str) -> f64 {
    let (p, h, total) = analyze_sentence(sentence);
    if total < 3 {
        return 0.0;
    }
    let total_markers = p + h;
    if total_markers == 0 {
        return 0.0;
    }
    (p as f64 - h as f64) / total_markers as f64
}

pub fn analyze_text(sentences: &[String]) -> Vec<f64> {
    sentences.iter().map(|s| will_index(s)).collect()
}
