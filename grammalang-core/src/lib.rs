use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

mod ontology;
mod error;
mod trace;
mod will_markers;

// ============ Экспорт в Python ============

#[pyfunction]
fn analyze_will(sentences: Vec<String>) -> PyResult<Vec<f64>> {
    Ok(will_markers::analyze_text(&sentences))
}

#[pymodule]
fn grammalang_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyze_will, m)?)?;
    Ok(())
}
