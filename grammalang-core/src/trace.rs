use serde::Serialize;
use std::sync::Mutex;
use std::collections::VecDeque;

#[derive(Debug, Clone, Serialize)]
pub struct VmEvent {
    pub event_type: String,
    pub node_id: String,
    pub pole_a: String,
    pub pole_b: String,
    pub status: String,
    pub reason: String,
}

pub struct TraceBuffer {
    events: Mutex<VecDeque<VmEvent>>,
}

impl TraceBuffer {
    pub fn new() -> Self {
        Self {
            events: Mutex::new(VecDeque::new()),
        }
    }

    pub fn push(&self, event: VmEvent) {
        let mut events = self.events.lock().unwrap();
        events.push_back(event);
        if events.len() > 1000 {
            events.pop_front();
        }
    }

    pub fn drain(&self) -> Vec<VmEvent> {
        let mut events = self.events.lock().unwrap();
        events.drain(..).collect()
    }
}
