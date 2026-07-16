import uuid
from src.core.image_profile import ImageProfile

class VisionNode:
    """
    Represents a single node in the VisionGraph hierarchy.
    """
    def __init__(self, node_id: str, label: str, parent_id: str = None, confidence: float = 1.0, attributes: dict = None):
        self.id = node_id
        self.label = label
        self.parent_id = parent_id
        self.confidence = confidence
        self.attributes = attributes or {}
        self.children = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "parent_id": self.parent_id,
            "confidence": self.confidence,
            "attributes": self.attributes,
            "children": [c.to_dict() for c in self.children]
        }

class VisionGraph:
    """
    Hierarchical representation of image understanding.
    Models semantic relationships (e.g. Human -> Face -> Eyes, Glasses).
    """
    def __init__(self):
        self.root = None
        self.nodes_map = {}

    def build_graph(self, profile: ImageProfile, context: dict) -> dict:
        """
        Constructs the VisionGraph based on ImageProfile and executed Runtimes in the context.
        """
        # Create root node for Scene
        scene_conf = profile.confidence.get("initial_segmentation", 0.90) if isinstance(profile.confidence, dict) else 0.90
        self.root = VisionNode(
            node_id="root",
            label=f"Scene: {profile.scene}",
            confidence=scene_conf,
            attributes={"background_complexity": profile.background.get("complexity", "low")}
        )
        self.nodes_map["root"] = self.root

        # Loop through subjects and build hierarchy
        for subj in profile.subject:
            subj_id = f"subj_{subj.lower()}"
            subj_conf = profile.confidence.get(subj, 0.88) if isinstance(profile.confidence, dict) else 0.88
            subj_node = VisionNode(
                node_id=subj_id,
                label=subj,
                parent_id="root",
                confidence=subj_conf,
                attributes={"materials": [m for m, val in profile.materials.items() if val > 0.1]}
            )
            self.root.children.append(subj_node)
            self.nodes_map[subj_id] = subj_node

            if subj == "Human":
                # Add Face
                face_ctx = context.get("face", {})
                if face_ctx.get("has_face"):
                    face_node = VisionNode(
                        node_id="face",
                        label="Face",
                        parent_id=subj_id,
                        confidence=face_ctx.get("confidence", 0.90),
                        attributes={
                            "pose": face_ctx.get("pose"),
                            "beard": face_ctx.get("beard"),
                            "ears": face_ctx.get("ears"),
                            "neck": face_ctx.get("neck")
                        }
                    )
                    subj_node.children.append(face_node)
                    self.nodes_map["face"] = face_node

                    # Add Eyes & Glasses
                    eye_ctx = context.get("eye", {})
                    if eye_ctx.get("has_eyes"):
                        eye_node = VisionNode(
                            node_id="eyes",
                            label="Eyes",
                            parent_id="face",
                            confidence=eye_ctx.get("confidence", 0.88),
                            attributes={
                                "blink_state": eye_ctx.get("blink_state"),
                                "reflections": eye_ctx.get("reflections")
                            }
                        )
                        face_node.children.append(eye_node)
                        self.nodes_map["eyes"] = eye_node

                        if eye_ctx.get("glasses"):
                            glasses_node = VisionNode(
                                node_id="glasses",
                                label="Glasses",
                                parent_id="eyes",
                                confidence=eye_ctx.get("confidence", 0.88) * 0.95,
                                attributes={"preserves_transparency": True}
                            )
                            eye_node.children.append(glasses_node)
                            self.nodes_map["glasses"] = glasses_node

                # Add Clothing
                cloth_ctx = context.get("clothing", {})
                if cloth_ctx.get("has_clothing"):
                    cloth_node = VisionNode(
                        node_id="clothing",
                        label=f"Clothing ({cloth_ctx.get('clothing_type', 'shirt')})",
                        parent_id=subj_id,
                        confidence=cloth_ctx.get("confidence", 0.85),
                        attributes={
                            "fabric_type": cloth_ctx.get("fabric_type"),
                            "mesh": cloth_ctx.get("mesh"),
                            "transparency": cloth_ctx.get("transparency")
                        }
                    )
                    subj_node.children.append(cloth_node)
                    self.nodes_map["clothing"] = cloth_node

                # Add Hair
                has_hair = profile.hair_fur.get("has_hair") or "hair" in context
                if has_hair:
                    hair_ctx = context.get("hair", {})
                    hair_node = VisionNode(
                        node_id="hair",
                        label="Hair",
                        parent_id=subj_id,
                        confidence=profile.confidence.get("fused_hair", 0.85) if isinstance(profile.confidence, dict) else 0.85,
                        attributes={
                            "hair_type": profile.hair_fur.get("hair_type"),
                            "density": profile.hair_fur.get("hair_density"),
                            "flyaways": profile.hair_fur.get("hair_flyaway_score", 0.0) > 0.3
                        }
                    )
                    subj_node.children.append(hair_node)
                    self.nodes_map["hair"] = hair_node

            elif subj == "Animal":
                # Add Animal Anatomy
                anat_ctx = context.get("animal_anatomy", {})
                if anat_ctx.get("has_anatomy"):
                    for feat in ["ears", "whiskers", "tail", "paws", "feathers"]:
                        if anat_ctx.get(feat):
                            feat_node = VisionNode(
                                node_id=f"anim_{feat}",
                                label=feat.capitalize(),
                                parent_id=subj_id,
                                confidence=anat_ctx.get("confidence", 0.85)
                            )
                            subj_node.children.append(feat_node)
                            self.nodes_map[f"anim_{feat}"] = feat_node

            elif subj == "Plant":
                # Add Plant Structures
                plant_ctx = context.get("plant", {})
                if plant_ctx.get("has_botanical"):
                    for feat in ["leaves", "stems", "flowers", "thorns", "needles"]:
                        if plant_ctx.get(feat):
                            feat_node = VisionNode(
                                node_id=f"plant_{feat}",
                                label=feat.capitalize(),
                                parent_id=subj_id,
                                confidence=plant_ctx.get("confidence", 0.85)
                            )
                            subj_node.children.append(feat_node)
                            self.nodes_map[f"plant_{feat}"] = feat_node

            elif subj in ["Product", "Vehicle"]:
                # Add Product Geometry features
                geom_ctx = context.get("product_geometry", {})
                if geom_ctx.get("has_geometry"):
                    if geom_ctx.get("straight_edges"):
                        se_node = VisionNode(
                            node_id="prod_straight",
                            label="Straight Edges",
                            parent_id=subj_id,
                            confidence=geom_ctx.get("confidence", 0.85),
                            attributes={"industrial_refinement": True}
                        )
                        subj_node.children.append(se_node)
                        self.nodes_map["prod_straight"] = se_node

                    if geom_ctx.get("circular_edges"):
                        ce_node = VisionNode(
                            node_id="prod_circular",
                            label="Circular Edges",
                            parent_id=subj_id,
                            confidence=geom_ctx.get("confidence", 0.85)
                        )
                        subj_node.children.append(ce_node)
                        self.nodes_map["prod_circular"] = ce_node

                    if geom_ctx.get("reflective_surfaces"):
                        re_node = VisionNode(
                            node_id="prod_reflective",
                            label="Reflective Surfaces",
                            parent_id=subj_id,
                            confidence=geom_ctx.get("confidence", 0.85),
                            attributes={"specular_reflection": True}
                        )
                        subj_node.children.append(re_node)
                        self.nodes_map["prod_reflective"] = re_node

        return self.root.to_dict() if self.root else {}
