import cv2
import numpy as np

class SubjectRegionGraph:
    """
    Creates a Subject Region Graph mapping semantic subject regions (skin, hair, fur, glass, fabric, etc.).
    """
    def __init__(self):
        pass

    def build_graph(self, mask, material_maps, edge_map=None, confidence_maps=None):
        """
        Builds region nodes and adjacency edges.
        material_maps: probability maps of shape (H, W, 12) or similar.
        Returns: dict representing region nodes, edges, and labeled_regions.
        """
        h, w = mask.shape[:2]
        nodes = []
        edges = []
        
        # Downscale for performance
        scale = 1.0
        if max(h, w) > 256:
            scale = 256.0 / max(h, w)
            mask_small = cv2.resize(mask, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            mats_small = cv2.resize(material_maps, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        else:
            mask_small = mask.copy()
            mats_small = material_maps.copy()
            
        sh, sw = mask_small.shape[:2]
        foreground = mask_small > 128
        
        # 10 material classes matching v2 SDK specification:
        # Skin, Hair, Fur, Fabric, Glass, Plastic, Metal, Leather, Lace, Feather
        material_names = [
            "Skin", "Hair", "Fur", "Fabric", "Glass", "Plastic",
            "Metal", "Leather", "Lace", "Feather"
        ]
        
        # Map material probabilities to node components
        labeled_regions = np.zeros((sh, sw), dtype=np.int32)
        region_counter = 1
        node_id_to_meta = {}
        
        for idx, name in enumerate(material_names):
            if idx >= mats_small.shape[2]:
                continue
            prob = mats_small[:, :, idx]
            # Region must be within foreground and probability > 0.2
            region_mask = (prob > 0.2) & foreground
            
            if np.count_nonzero(region_mask) < 20:
                continue
                
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(region_mask.astype(np.uint8))
            for i in range(1, num_labels):
                area = int(stats[i, cv2.CC_STAT_AREA])
                if area < 15:
                    continue
                # Assign unique ID
                r_id = region_counter
                labeled_regions[labels == i] = r_id
                
                bx = int(stats[i, cv2.CC_STAT_LEFT] / scale)
                by = int(stats[i, cv2.CC_STAT_TOP] / scale)
                bw = int(stats[i, cv2.CC_STAT_WIDTH] / scale)
                bh = int(stats[i, cv2.CC_STAT_HEIGHT] / scale)
                
                avg_prob = float(np.mean(prob[labels == i]))
                
                # Estimate dominant edge type
                edge_type = "Soft"
                if edge_map is not None:
                    try:
                        edge_map_small = cv2.resize(edge_map, (sw, sh), interpolation=cv2.INTER_NEAREST)
                        region_edges = edge_map_small[labels == i]
                        region_edges = region_edges[region_edges >= 0]
                        if len(region_edges) > 0:
                            dom_edge_val = int(np.bincount(region_edges).argmax())
                            edge_classes = ["Hard", "Soft", "Hair", "Fur", "Fabric", "Transparent", "Reflection", "Motion Blur", "Shadow", "Whisker"]
                            if 0 <= dom_edge_val < len(edge_classes):
                                edge_type = edge_classes[dom_edge_val]
                    except Exception as e:
                        pass
                
                # Transparency estimation
                transparency = 0.0
                if name in ["Glass", "Plastic", "Lace", "Feather"]:
                    transparency = avg_prob
                elif confidence_maps is not None and "transparency_confidence" in confidence_maps:
                    try:
                        trans_map_small = cv2.resize(confidence_maps["transparency_confidence"], (sw, sh), interpolation=cv2.INTER_LINEAR)
                        transparency = float(np.mean(trans_map_small[labels == i]))
                    except Exception:
                        pass
                        
                # Confidence estimation
                confidence = avg_prob
                if confidence_maps is not None and "material_confidence" in confidence_maps:
                    try:
                        conf_map_small = cv2.resize(confidence_maps["material_confidence"], (sw, sh), interpolation=cv2.INTER_LINEAR)
                        confidence = float(np.mean(conf_map_small[labels == i]))
                    except Exception:
                        pass
                        
                refinement_profile = {
                    "label": name,
                    "edge_type": edge_type,
                    "transparency": transparency,
                    "confidence": confidence
                }
                
                node_id_to_meta[r_id] = {
                    "id": r_id,
                    "label": name,
                    "box": [by, by + bh, bx, bx + bw],
                    "area": int(area / (scale**2)),
                    "avg_prob": avg_prob,
                    
                    # Upgraded v3 properties
                    "semantic_class": name,
                    "material": name,
                    "edge_type": edge_type,
                    "transparency": transparency,
                    "confidence": confidence,
                    "refinement_profile": refinement_profile
                }
                nodes.append(node_id_to_meta[r_id])
                region_counter += 1
                
        # Connect nodes if adjacent
        for r_id1, meta1 in node_id_to_meta.items():
            mask1 = (labeled_regions == r_id1).astype(np.uint8)
            dilated = cv2.dilate(mask1, np.ones((3,3), np.uint8))
            for r_id2, meta2 in node_id_to_meta.items():
                if r_id1 >= r_id2:
                    continue
                mask2 = (labeled_regions == r_id2).astype(np.uint8)
                if np.any((dilated > 0) & (mask2 > 0)):
                    edges.append((r_id1, r_id2))
                    
        # If graph is empty, add a default fallback node representing the entire subject
        if not nodes:
            nodes.append({
                "id": 1,
                "label": "general",
                "box": [0, h, 0, w],
                "area": int(np.count_nonzero(mask)),
                "avg_prob": 1.0,
                
                # Upgraded v3 properties
                "semantic_class": "general",
                "material": "general",
                "edge_type": "Soft",
                "transparency": 0.0,
                "confidence": 1.0,
                "refinement_profile": {"label": "general", "edge_type": "Soft", "transparency": 0.0, "confidence": 1.0}
            })
            # Initialize default labeled regions
            labeled_regions = (mask_small > 128).astype(np.int32)
            
        return {
            "nodes": nodes,
            "edges": edges,
            "labeled_regions": labeled_regions
        }

