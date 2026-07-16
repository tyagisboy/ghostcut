class RuntimeCostModel:
    """
    Estimates latency and memory costs per cognitive runtime category.
    """
    def __init__(self):
        # Base relative cost mapping (relative weight units)
        self.costs = {
            "scene": {"latency": 5, "memory": 2},
            "subject": {"latency": 10, "memory": 5},
            "background": {"latency": 8, "memory": 4},
            "material": {"latency": 15, "memory": 8},
            "edge": {"latency": 20, "memory": 12},
            "hair": {"latency": 45, "memory": 25},
            "fur": {"latency": 40, "memory": 22},
            "glass": {"latency": 35, "memory": 20}
        }

    def estimate_cost(self, active_runtimes: list) -> dict:
        total_latency = 0
        total_memory = 0
        for rt in active_runtimes:
            rt_cost = self.costs.get(rt.lower(), {"latency": 10, "memory": 5})
            total_latency += rt_cost["latency"]
            total_memory += rt_cost["memory"]
            
        return {
            "estimated_latency_score": total_latency,
            "estimated_memory_score": total_memory
        }
