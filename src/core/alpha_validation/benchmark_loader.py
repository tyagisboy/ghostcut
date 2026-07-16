from src.core.alpha_validation.benchmark_manifest import BenchmarkManifest

class BenchmarkLoader:
    """
    Retrieves entries and registers active configurations for execution runner.
    """
    def __init__(self):
        self.manifest = BenchmarkManifest()

    def load_active_benchmarks(self) -> dict:
        return self.manifest.manifest
