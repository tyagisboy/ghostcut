class BeliefNode:
    """
    Represents a verified or refuted semantic belief within the Cognitive Vision System.
    """
    def __init__(self, entity: str, status: str = "DEFERRED", confidence: float = 0.0, parent_id: str = None):
        self.id = entity.lower()
        self.entity = entity
        self.status = status  # ACCEPTED, REJECTED, DEFERRED
        self.confidence = float(confidence)
        self.parent_id = parent_id
        self.supporting_evidence = []
        self.contradicting_evidence = []
        self.children = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.entity,
            "status": self.status,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "children": [c.to_dict() for c in self.children]
        }

class BeliefGraph:
    """
    Hierarchical graph organizing BeliefNodes based on semantic structures.
    """
    def __init__(self):
        self.nodes = {}
        # Set up default root anchors
        self.root_nodes = []

    def add_belief(self, entity: str, parent_id: str = None) -> BeliefNode:
        node_id = entity.lower()
        if node_id not in self.nodes:
            node = BeliefNode(entity, parent_id=parent_id)
            self.nodes[node_id] = node
            if parent_id and parent_id.lower() in self.nodes:
                self.nodes[parent_id.lower()].children.append(node)
            else:
                self.root_nodes.append(node)
        return self.nodes[node_id]

    def get_belief(self, entity: str) -> BeliefNode:
        return self.nodes.get(entity.lower())

    def get_root_belief(self) -> dict:
        """
        Compiles the primary root belief dictionary hierarchy.
        """
        # If multiple root nodes, return a synthetic Scene node
        if len(self.root_nodes) == 1:
            return self.root_nodes[0].to_dict()
            
        return {
            "id": "scene_root",
            "label": "Scene Root",
            "status": "ACCEPTED",
            "confidence": 1.0,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "children": [r.to_dict() for r in self.root_nodes]
        }
