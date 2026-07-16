from src.core.runtime_registry import RuntimeRegistry

class RuntimeScheduler:
    """
    Orchestrates execution graph scheduling, dependency sorting, and dynamic pipeline configuration.
    Determines execution plans, sorting them topologically and monitoring CPU savings.
    """
    def __init__(self, registry: RuntimeRegistry = None):
        self.registry = registry if registry is not None else RuntimeRegistry()

    def resolve_dependencies(self, runtime_ids: list) -> list:
        """
        Sorts the requested runtime IDs topologically based on dependency graphs.
        Uses a standard cycle-detecting Depth-First Search.
        """
        ordered = []
        visited = set()
        temp = set()

        def visit(node_id):
            if node_id in temp:
                raise ValueError(f"Cyclic dependency detected at runtime ID: '{node_id}'!")
            if node_id not in visited:
                temp.add(node_id)
                
                # Fetch runtime class from registry
                runtime_class = self.registry.get_runtime(node_id)
                if runtime_class is None:
                    raise KeyError(f"Runtime ID '{node_id}' is not registered in the Registry.")
                
                # Query dependencies
                meta = runtime_class().get_metadata()
                for dep in meta.get("dependencies", []):
                    # Only resolve if the dependency is also requested
                    if dep in runtime_ids:
                        visit(dep)
                        
                temp.remove(node_id)
                visited.add(node_id)
                ordered.append(node_id)

        for rid in runtime_ids:
            visit(rid)
        return ordered

    def get_execution_plan(self, scene_name: str, subjects: list, detected_regions: list = None) -> dict:
        """
        Compiles the topological plan dynamically based on Scene, Subject, and physical detected regions.
        Returns:
            plan: list of topologically sorted runtime IDs to execute.
            skipped: list of runtime IDs that were omitted.
            cpu_savings_percent: float percentage of CPU costs saved.
        """
        # Always execute core pre-inference foundation modules
        requested = ["scene", "subject", "background"]

        # Post-inference foundation
        requested.append("material")
        requested.append("edge")
        requested.append("confidence_fusion")

        # Rationale trace log
        trace = []
        trace.append(f"Scheduling started for scene: '{scene_name}' with subjects: {subjects}")

        # Determine subject context
        has_human = "Human" in subjects or scene_name in ["Studio Portrait", "Outdoor Portrait", "Backlit Portrait"]
        has_animal = "Animal" in subjects or scene_name in ["Pet"]
        has_plant = "Plant" in subjects or "Plant" in scene_name
        has_product = "Product" in subjects or "Vehicle" in subjects or scene_name in ["Product", "Vehicle"]

        # Dynamically add domain-specific modules
        if has_human:
            requested.append("face")
            requested.append("eye")
            requested.append("clothing")
            
            # Phase 6 & Phase 2: Region-First Execution Pruning
            if detected_regions is None or "hair" in detected_regions:
                requested.append("hair")
            else:
                trace.append("Pruned hair sensor: No hair regions detected.")
                
            trace.append("Human subject context identified: requested face, eye, clothing sensors")
            
        if has_animal:
            requested.append("animal_anatomy")
            
            if detected_regions is None or "fur" in detected_regions:
                requested.append("fur")
            else:
                trace.append("Pruned fur sensor: No fur regions detected.")
                
            trace.append("Animal subject context identified: requested animal_anatomy sensors")
            
        if has_plant:
            requested.append("plant")
            trace.append("Plant subject context identified: requested plant sensors")
            
        if has_product:
            requested.append("product_geometry")
            trace.append("Product subject context identified: requested product_geometry sensors")

        # Resolve topologically
        plan = self.resolve_dependencies(requested)
        trace.append(f"Topological sorting completed. Execution plan: {plan}")

        # Find skipped runtimes and calculate cost savings
        all_registered = list(self.registry.list_runtimes().keys())
        skipped = [r for r in all_registered if r not in plan]
        
        skipped_reasons = {}
        for r in skipped:
            if r in ["face", "eye", "clothing", "hair"] and not has_human:
                skipped_reasons[r] = "Skipped: Human subject context not active"
            elif r == "hair" and has_human:
                skipped_reasons[r] = "Skipped: Hair regions not detected"
            elif r in ["animal_anatomy", "fur"] and not has_animal:
                skipped_reasons[r] = "Skipped: Animal subject context not active"
            elif r == "fur" and has_animal:
                skipped_reasons[r] = "Skipped: Fur regions not detected"
            elif r == "plant" and not has_plant:
                skipped_reasons[r] = "Skipped: Plant subject context not active"
            elif r == "product_geometry" and not has_product:
                skipped_reasons[r] = "Skipped: Product subject context not active"
            else:
                skipped_reasons[r] = "Skipped: Pre-inference scheduler prune override"

        # Calculate costs based on metadata
        total_cost = 0.0
        skipped_cost = 0.0

        for r_id in all_registered:
            runtime_class = self.registry.get_runtime(r_id)
            if runtime_class is not None:
                cost = float(runtime_class().get_metadata().get("execution_cost", 1.0))
                total_cost += cost
                if r_id in skipped:
                    skipped_cost += cost

        savings = (skipped_cost / total_cost * 100.0) if total_cost > 0 else 0.0
        trace.append(f"Pruning complete. Saved {savings:.1f}% execution complexity.")

        return {
            "plan": plan,
            "skipped": skipped,
            "skipped_reasons": skipped_reasons,
            "cpu_savings_percent": savings,
            "execution_trace": trace
        }
