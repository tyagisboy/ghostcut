from src.core.evidence_graph import EvidenceGraph
from src.core.belief_graph import BeliefGraph

class ConsensusEngine:
    """
    Evaluates evidence nodes, resolves semantic contradictions,
    and updates belief node statuses accordingly.
    """
    def __init__(self):
        pass

    def resolve_conflicts(self, evidence_graph: EvidenceGraph, belief_graph: BeliefGraph) -> dict:
        """
        Executes consensus rules to filter competing sensory claims.
        """
        all_evidence = {ev["observation"].lower(): ev for ev in evidence_graph.get_all_nodes()}
        
        decisions_logged = []
        consensus_score = 1.0

        # Build initial list of beliefs based on evidence
        for obs_name, ev in all_evidence.items():
            belief_graph.add_belief(ev["observation"])

        # Execute Contradiction Rules
        # Rule 1: Human + Fur contradiction -> Reject Fur
        if "human" in all_evidence and "fur" in all_evidence:
            h_ev = all_evidence["human"]
            f_ev = all_evidence["fur"]
            
            fur_node = belief_graph.get_belief("Fur")
            human_node = belief_graph.get_belief("Human")
            
            if h_ev["confidence"] >= f_ev["confidence"]:
                fur_node.status = "REJECTED"
                fur_node.contradicting_evidence.append(h_ev["id"])
                human_node.status = "ACCEPTED"
                human_node.supporting_evidence.append(h_ev["id"])
                decisions_logged.append("Reject Fur in favor of Human")
                consensus_score -= 0.15
            else:
                human_node.status = "REJECTED"
                human_node.contradicting_evidence.append(f_ev["id"])
                fur_node.status = "ACCEPTED"
                fur_node.supporting_evidence.append(f_ev["id"])
                decisions_logged.append("Reject Human in favor of Fur")
                consensus_score -= 0.15

        # Rule 2: Plant + Skin -> Reject Skin
        if "plant" in all_evidence and "skin" in all_evidence:
            p_ev = all_evidence["plant"]
            s_ev = all_evidence["skin"]
            
            skin_node = belief_graph.get_belief("Skin")
            plant_node = belief_graph.get_belief("Plant")
            
            skin_node.status = "REJECTED"
            skin_node.contradicting_evidence.append(p_ev["id"])
            plant_node.status = "ACCEPTED"
            plant_node.supporting_evidence.append(p_ev["id"])
            decisions_logged.append("Reject Skin in favor of Plant")
            consensus_score -= 0.10

        # Rule 3: Product + Hair -> Reject Hair
        if "product" in all_evidence and "hair" in all_evidence:
            p_ev = all_evidence["product"]
            h_ev = all_evidence["hair"]
            
            hair_node = belief_graph.get_belief("Hair")
            prod_node = belief_graph.get_belief("Product")
            
            hair_node.status = "REJECTED"
            hair_node.contradicting_evidence.append(p_ev["id"])
            prod_node.status = "ACCEPTED"
            prod_node.supporting_evidence.append(p_ev["id"])
            decisions_logged.append("Reject Hair in favor of Product")
            consensus_score -= 0.10

        # Rule 4: Default Acceptance for single evidence
        for node in belief_graph.nodes.values():
            if node.status == "DEFERRED":
                obs_lower = node.entity.lower()
                if obs_lower in all_evidence:
                    node.status = "ACCEPTED"
                    node.supporting_evidence.append(all_evidence[obs_lower]["id"])
                    node.confidence = all_evidence[obs_lower]["confidence"]

        # Ensure consensus score is bounded
        import numpy as np
        consensus_score = float(np.clip(consensus_score, 0.4, 1.0))

        return {
            "consensus_score": consensus_score,
            "decisions": decisions_logged
        }
