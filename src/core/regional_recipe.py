class RegionalRecipeEngine:
    """
    Compiles distinct, localized matting parameter policies for each node
    detected in the SubjectRegionGraph, integrating hierarchical overrides from the VisionGraph.
    """
    def __init__(self):
        pass

    def compile_regional_policies(self, graph, global_recipe, vision_graph=None):
        """
        Generates individual region parameter maps, factoring in VisionGraph hierarchy details.
        """
        region_policies = {}
        nodes = graph.get("nodes", [])
        
        # Map vision nodes by ID for direct lookup
        vision_nodes = {}
        if vision_graph:
            def traverse(node):
                if node and "id" in node:
                    vision_nodes[node["id"]] = node
                    for child in node.get("children", []):
                        traverse(child)
            traverse(vision_graph)
            
        for node in nodes:
            label = node["label"]
            r_id = node["id"]
            
            # Start with default copy of global recipe parameters
            params = {
                "bg_thresh": global_recipe.bg_thresh if hasattr(global_recipe, "bg_thresh") else 15,
                "fg_thresh": global_recipe.fg_thresh if hasattr(global_recipe, "fg_thresh") else 240,
                "erode_size": global_recipe.erode_size,
                "sharpness": global_recipe.sharpness,
                "preserve_transparency": global_recipe.preserve_transparency,
                "focus_thresh": global_recipe.focus_thresh,
                "decontaminate": global_recipe.decontaminate
            }
            
            # Specialize parameters per region type (Inherited / Overridden by VisionGraph nodes)
            if label == "Hair":
                params["bg_thresh"] = 15
                params["fg_thresh"] = 250
                params["erode_size"] = 9
                params["sharpness"] = 0
                params["decontaminate"] = True
                
                # Check for flyaways in hair node
                if "hair" in vision_nodes:
                    attrs = vision_nodes["hair"].get("attributes", {})
                    if attrs.get("flyaways"):
                        params["erode_size"] = 12
                        params["fg_thresh"] = 253
                        
            elif label == "Fur":
                params["bg_thresh"] = 20
                params["fg_thresh"] = 248
                params["erode_size"] = 7
                params["sharpness"] = 0
                params["decontaminate"] = True
                
                # Whiskers adjustment
                if "anim_whiskers" in vision_nodes:
                    params["erode_size"] = 10
                    params["fg_thresh"] = 252
                    
            elif label == "Skin":
                params["bg_thresh"] = 40
                params["fg_thresh"] = 240
                params["erode_size"] = 2
                params["sharpness"] = 3
                params["decontaminate"] = False
                
                # Beard override on skin
                if "face" in vision_nodes:
                    face_attrs = vision_nodes["face"].get("attributes", {})
                    if face_attrs.get("beard"):
                        params["erode_size"] = 4
                        params["bg_thresh"] = 25
                        
            elif label == "Glass":
                params["preserve_transparency"] = True
                params["bg_thresh"] = 25
                params["fg_thresh"] = 230
                params["erode_size"] = 5
                params["decontaminate"] = True
                
                # Eyeglasses override
                if "glasses" in vision_nodes:
                    params["preserve_transparency"] = True
                    params["fg_thresh"] = 220
                    
            elif label == "Metal" or label == "Plastic":
                params["erode_size"] = 1
                params["sharpness"] = 4
                params["decontaminate"] = False
                
                # Straight edges geometry optimization
                if "prod_straight" in vision_nodes:
                    params["sharpness"] = 5
                    params["erode_size"] = 0
                    
            elif label == "Fabric":
                params["bg_thresh"] = 30
                params["fg_thresh"] = 235
                params["erode_size"] = 4
                params["sharpness"] = 1
                params["decontaminate"] = False
                
                # Semi-transparent fabric override
                if "clothing" in vision_nodes:
                    c_attrs = vision_nodes["clothing"].get("attributes", {})
                    if c_attrs.get("mesh") or c_attrs.get("transparency"):
                        params["preserve_transparency"] = True
                        params["fg_thresh"] = 225
                        
            region_policies[r_id] = params
            
        return region_policies


