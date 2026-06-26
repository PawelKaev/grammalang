pub mod ontology;
pub mod error;
pub mod trace;

use ontology::*;
use trace::{TraceBuffer, VmEvent};
use pyo3::prelude::*;
use std::sync::Arc;

#[pyfunction]
fn analyze_text(material: String) -> PyResult<String> {
    let mut ctx = OntologicalContext::new();
    let trace = TraceBuffer::new();

    let templates = vec![
        ("свобода", "Свобода", 0.8f32),
        ("необходимость", "Необходимость", 0.4),
        ("пространство", "Пространство", 0.6),
        ("время", "Время", 0.7),
        ("единство", "Единство", 0.5),
        ("множество", "Множество", 0.5),
        ("субъект", "Субъект", 0.9),
        ("объект", "Объект", 0.3),
        ("дух", "Дух", 0.85),
        ("материя", "Материя", 0.35),
    ];

    let text_lower = material.to_lowercase();
    let mut found: Vec<Substance> = Vec::new();

    for (keyword, name, energy) in &templates {
        if text_lower.contains(keyword) {
            let id = SubstanceId(keyword.to_string());
            let sub = Substance {
                id: id.clone(),
                name: name.to_string(),
                energy: *energy,
            };
            ctx.add_substance(sub.clone());
            found.push(sub);
        }
    }

    if found.len() < 2 {
        let s1 = Substance {
            id: SubstanceId("свобода".into()),
            name: "Свобода".into(),
            energy: 0.7,
        };
        let s2 = Substance {
            id: SubstanceId("необходимость".into()),
            name: "Необходимость".into(),
            energy: 0.3,
        };
        ctx.add_substance(s1.clone());
        ctx.add_substance(s2.clone());
        found.push(s1);
        found.push(s2);
    }

    for i in 0..found.len() {
        for j in (i + 1)..found.len() {
            let a = &found[i];
            let b = &found[j];
            let reason = if text_lower.contains("антиномия") {
                "antinomy"
            } else if text_lower.contains("диалектика") {
                "dialectic"
            } else {
                "contradiction"
            };
            let node_id = ctx
                .hold_contradiction(a.id.clone(), b.id.clone(), reason.to_string())
                .unwrap();

            trace.push(VmEvent {
                event_type: "hold_created".into(),
                node_id: node_id.clone(),
                pole_a: a.id.0.clone(),
                pole_b: b.id.0.clone(),
                status: "held".into(),
                reason: reason.to_string(),
            });

            if material.len() % 2 == 0 {
                let _ = ctx.resolve_tension(&node_id, a.id.clone());
                trace.push(VmEvent {
                    event_type: "resolved".into(),
                    node_id: node_id.clone(),
                    pole_a: a.id.0.clone(),
                    pole_b: b.id.0.clone(),
                    status: "resolved".into(),
                    reason: reason.to_string(),
                });
            }
        }
    }

    ctx.to_json()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

#[pyfunction]
fn analyze_text_with_trace(material: String) -> PyResult<(String, String)> {
    let mut ctx = OntologicalContext::new();
    let trace = TraceBuffer::new();

    let templates = vec![
        ("свобода", "Свобода", 0.8f32),
        ("необходимость", "Необходимость", 0.4),
        ("пространство", "Пространство", 0.6),
        ("время", "Время", 0.7),
        ("единство", "Единство", 0.5),
        ("множество", "Множество", 0.5),
        ("субъект", "Субъект", 0.9),
        ("объект", "Объект", 0.3),
        ("дух", "Дух", 0.85),
        ("материя", "Материя", 0.35),
    ];

    let text_lower = material.to_lowercase();
    let mut found: Vec<Substance> = Vec::new();

    for (keyword, name, energy) in &templates {
        if text_lower.contains(keyword) {
            let id = SubstanceId(keyword.to_string());
            let sub = Substance {
                id: id.clone(),
                name: name.to_string(),
                energy: *energy,
            };
            ctx.add_substance(sub.clone());
            found.push(sub);
        }
    }

    if found.len() < 2 {
        let s1 = Substance {
            id: SubstanceId("свобода".into()),
            name: "Свобода".into(),
            energy: 0.7,
        };
        let s2 = Substance {
            id: SubstanceId("необходимость".into()),
            name: "Необходимость".into(),
            energy: 0.3,
        };
        ctx.add_substance(s1.clone());
        ctx.add_substance(s2.clone());
        found.push(s1);
        found.push(s2);
    }

    for i in 0..found.len() {
        for j in (i + 1)..found.len() {
            let a = &found[i];
            let b = &found[j];
            let reason = if text_lower.contains("антиномия") {
                "antinomy"
            } else if text_lower.contains("диалектика") {
                "dialectic"
            } else {
                "contradiction"
            };
            let node_id = ctx
                .hold_contradiction(a.id.clone(), b.id.clone(), reason.to_string())
                .unwrap();

            trace.push(VmEvent {
                event_type: "hold_created".into(),
                node_id: node_id.clone(),
                pole_a: a.id.0.clone(),
                pole_b: b.id.0.clone(),
                status: "held".into(),
                reason: reason.to_string(),
            });

            if material.len() % 2 == 0 {
                let _ = ctx.resolve_tension(&node_id, a.id.clone());
                trace.push(VmEvent {
                    event_type: "resolved".into(),
                    node_id: node_id.clone(),
                    pole_a: a.id.0.clone(),
                    pole_b: b.id.0.clone(),
                    status: "resolved".into(),
                    reason: reason.to_string(),
                });
            }
        }
    }

    let ctx_json = ctx
        .to_json()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let trace_json = serde_json::to_string(&trace.drain())
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok((ctx_json, trace_json))
}

#[pymodule]
fn grammalang_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyze_text, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_text_with_trace, m)?)?;
    Ok(())
}
