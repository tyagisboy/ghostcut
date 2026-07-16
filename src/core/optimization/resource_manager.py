import multiprocessing

try:
    import psutil
except ImportError:
    psutil = None

class AdaptiveResourceManager:
    """
    Analyzes hardware resources (available memory, processor cores, and model caches)
    to select the best runtime execution configuration level: Eco, Balanced, Quality, or Ultra.
    """
    def __init__(self):
        pass

    def get_hardware_profile(self) -> dict:
        if psutil is not None:
            total_ram_gb = psutil.virtual_memory().total / (1024.0 ** 3)
        else:
            total_ram_gb = 16.0  # Safe default baseline
            
        cpu_cores = multiprocessing.cpu_count()
        
        # CPU-first primary targets detection
        cuda_available = False
        directml_available = False
        
        # Determine execution profile
        if total_ram_gb < 8.0 or cpu_cores <= 4:
            profile = "Eco"
        elif total_ram_gb <= 16.0:
            profile = "Balanced"
        elif total_ram_gb <= 32.0:
            profile = "Quality"
        else:
            profile = "Ultra"
            
        return {
            "total_ram_gb": float(total_ram_gb),
            "cpu_cores": int(cpu_cores),
            "cuda_available": cuda_available,
            "directml_available": directml_available,
            "selected_profile": profile
        }
