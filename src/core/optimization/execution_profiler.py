class ExecutionProfiler:
    """
    Maintains a record of executed modules, pipeline paths, and caching logs.
    """
    def __init__(self):
        self.traces = []

    def record_trace(self, runtime_id: str, status: str, duration_ms: float) -> None:
        self.traces.append({
            "runtime_id": runtime_id,
            "status": status,
            "duration_ms": float(duration_ms)
        })

    def get_traces(self) -> list:
        return self.traces

    def clear_traces(self) -> None:
        self.traces.clear()
