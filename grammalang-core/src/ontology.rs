use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use crate::error::GrammarError;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct SubstanceId(pub String);

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Substance {
    pub id: SubstanceId,
    pub name: String,
    pub energy: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Modus {
    pub name: String,
    pub value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TensionStatus {
    #[serde(rename = "held")]
    Held,
    #[serde(rename = "resolved")]
    Resolved(SubstanceId),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TensionNode {
    pub id: String,
    pub pole_a: SubstanceId,
    pub pole_b: SubstanceId,
    pub reason: String,
    pub status: TensionStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct OntologicalContext {
    substances: BTreeMap<SubstanceId, Substance>,
    modi: BTreeMap<SubstanceId, Vec<Modus>>,
    tensions: Vec<TensionNode>,
}

impl OntologicalContext {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_substance(&mut self, substance: Substance) {
        self.substances.insert(substance.id.clone(), substance);
    }

    pub fn get_substance(&self, id: &SubstanceId) -> Option<&Substance> {
        self.substances.get(id)
    }

    pub fn substances(&self) -> &BTreeMap<SubstanceId, Substance> {
        &self.substances
    }

    pub fn tensions(&self) -> &Vec<TensionNode> {
        &self.tensions
    }

    pub fn hold_contradiction(
        &mut self,
        pole_a: SubstanceId,
        pole_b: SubstanceId,
        reason: String,
    ) -> Result<String, GrammarError> {
        if !self.substances.contains_key(&pole_a) || !self.substances.contains_key(&pole_b) {
            return Err(GrammarError::SubstanceNotFound(
                "One or both substances not found".to_string(),
            ));
        }

        let id = format!("t_{}", self.tensions.len());
        let node = TensionNode {
            id: id.clone(),
            pole_a,
            pole_b,
            reason,
            status: TensionStatus::Held,
        };
        self.tensions.push(node);
        Ok(id)
    }

    pub fn resolve_tension(
        &mut self,
        node_id: &str,
        winner: SubstanceId,
    ) -> Result<(), GrammarError> {
        let node = self
            .tensions
            .iter_mut()
            .find(|n| n.id == node_id)
            .ok_or_else(|| GrammarError::TensionNodeNotFound(node_id.to_string()))?;

        if node.status != TensionStatus::Held {
            return Err(GrammarError::TensionAlreadyResolved(node_id.to_string()));
        }

        if winner != node.pole_a && winner != node.pole_b {
            return Err(GrammarError::InvalidWinner);
        }

        node.status = TensionStatus::Resolved(winner);
        Ok(())
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }
}
