import sys
import numpy as np
from src.core.evidence_graph import EvidenceGraph
from src.core.belief_graph import BeliefGraph
from src.core.consensus_engine import ConsensusEngine
from src.core.strategy_engine import StrategyEngine
from src.core.self_critic_engine import SelfCriticEngine

def run_v5_0_benchmarks():
    print("[*] Initializing Cognitive Architecture v5.0 Benchmark Suite...")

    # 1. Test Evidence Graph & Collection
    print("[*] Testing Evidence Graph node generation...")
    eg = EvidenceGraph()
    
    # Simulate conflicting evidence: Sensor Hair vs. Sensor Fur
    eg.add_node("scene", "Studio Portrait", 0.95, ["high-res"])
    eg.add_node("subject", "Human", 0.92, ["bounding_box"])
    eg.add_node("hair", "Hair", 0.88, ["curly_strands"])
    eg.add_node("fur", "Fur", 0.72, ["furry_texture"]) # Contradictory observation
    
    assert len(eg.get_all_nodes()) == 4
    print("[OK] Evidence Graph successfully registered sensory inputs.")

    # 2. Test Consensus Engine Contradiction Resolution
    print("\n[*] Testing Consensus Engine conflict resolution...")
    bg = BeliefGraph()
    consensus = ConsensusEngine()
    
    res = consensus.resolve_conflicts(eg, bg)
    
    # Conflict between Human and Fur should ACCEPT Human and REJECT Fur
    human_belief = bg.get_belief("Human")
    fur_belief = bg.get_belief("Fur")
    
    assert human_belief.status == "ACCEPTED"
    assert fur_belief.status == "REJECTED"
    assert "ev_subject_human" in human_belief.supporting_evidence
    assert "ev_subject_human" in fur_belief.contradicting_evidence
    assert res["consensus_score"] < 1.0
    print("[OK] Consensus Engine successfully resolved Human+Fur contradiction.")

    # 3. Test Belief Graph Hierarchical Tree Compilation
    print("\n[*] Testing Belief Graph parent-child nesting...")
    # Add Face under Human child node, and Glasses under Face
    bg.add_belief("Face", parent_id="human")
    bg.add_belief("Glasses", parent_id="face")
    
    # Force accepted status on glasses for testing
    bg.get_belief("Glasses").status = "ACCEPTED"
    
    root_dict = bg.get_root_belief()
    # Check tree structure
    assert root_dict["label"] == "Scene Root" or root_dict["label"] == "Human"
    
    # Retrieve human child list
    human_children = [c["label"] for c in root_dict["children"] if c["label"] == "Human"]
    if not human_children:
        # If human itself is a root node
        human_node = root_dict
    else:
        human_node = [c for c in root_dict["children"] if c["label"] == "Human"][0]
        
    face_children = [c["label"] for c in human_node["children"]]
    assert "Face" in face_children
    print("[OK] Belief Graph hierarchical tree conformed successfully.")

    # 4. Test Strategy Engine Compiler
    print("\n[*] Testing Strategy Engine output compilation...")
    strat_engine = StrategyEngine()
    strategy = strat_engine.compile_strategy(bg)
    
    # Active runtimes should include face, eye, clothing, hair because Human is accepted
    assert "face" in strategy.active_runtimes
    assert "clothing" in strategy.active_runtimes
    # Active runtimes should NOT include fur
    assert "fur" not in strategy.active_runtimes
    # Transparency should be preserved because Glasses is accepted
    assert strategy.params["preserve_transparency"] is True
    print("[OK] Strategy Engine successfully translated beliefs to active runtimes.")

    # 5. Test Self-Critic Engine Evaluation
    print("\n[*] Testing Self-Critic Engine output evaluation...")
    critic = SelfCriticEngine()
    
    mock_mask = np.zeros((100, 100), dtype=np.uint8)
    # Simulate high quality metrics
    metrics_good = {
        "edge_score": 0.95,
        "alpha_score": 0.93,
        "stability_score": 0.99,
        "halo_spill_score": 0.94,
        "transparency_score": 0.96,
        "consistency_score": 0.98
    }
    critic_good = critic.criticize(mock_mask, metrics_good)
    assert critic_good["quality_grade"] == "A"
    assert critic_good["repair_needed"] is False
    
    # Simulate failing metrics (low stability due to floating pixels)
    metrics_bad = dict(metrics_good)
    metrics_bad["stability_score"] = 0.80
    critic_bad = critic.criticize(mock_mask, metrics_bad)
    assert critic_bad["quality_grade"] != "A"
    assert critic_bad["repair_needed"] is True
    assert any("stability" in f.lower() for f in critic_bad["failures"])
    print("[OK] Self-Critic Engine successfully evaluated quality metrics and flagged anomalies.")

    print("\n======================================")
    print("Cognitive Architecture v5.0 benchmarks completed: ALL PASSED.")
    print("======================================")
    return True

if __name__ == "__main__":
    success = run_v5_0_benchmarks()
    sys.exit(0 if success else 1)
