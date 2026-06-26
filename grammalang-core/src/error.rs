use thiserror::Error;

#[derive(Error, Debug)]
pub enum GrammarError {
    #[error("Substance not found: {0}")]
    SubstanceNotFound(String),

    #[error("Tension node not found: {0}")]
    TensionNodeNotFound(String),

    #[error("Tension node already resolved: {0}")]
    TensionAlreadyResolved(String),

    #[error("Winner must be one of the tension poles")]
    InvalidWinner,

    #[error("Parse error: {0}")]
    ParseError(String),
}
