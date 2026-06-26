use grammalang_core::ontology::*;

#[test]
fn test_hold_and_resolve_tension() {
    let mut ctx = OntologicalContext::new();

    let s1 = Substance {
        id: SubstanceId("freedom".to_string()),
        name: "Freedom".to_string(),
        energy: 0.7,
    };
    let s2 = Substance {
        id: SubstanceId("necessity".to_string()),
        name: "Necessity".to_string(),
        energy: 0.3,
    };

    ctx.add_substance(s1.clone());
    ctx.add_substance(s2.clone());

    let node_id = ctx
        .hold_contradiction(
            SubstanceId("freedom".to_string()),
            SubstanceId("necessity".to_string()),
            "antinomy".to_string(),
        )
        .expect("Failed to hold contradiction");

    assert_eq!(node_id, "t_0");
    assert_eq!(ctx.tensions().len(), 1);
    assert_eq!(ctx.tensions()[0].status, TensionStatus::Held);

    ctx.resolve_tension(&node_id, SubstanceId("freedom".to_string()))
        .expect("Failed to resolve tension");

    assert_eq!(
        ctx.tensions()[0].status,
        TensionStatus::Resolved(SubstanceId("freedom".to_string()))
    );
}
