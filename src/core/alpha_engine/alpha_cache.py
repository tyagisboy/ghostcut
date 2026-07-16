import numpy as np

class AlphaCache:
    """
    Caches intermediate matrices, tiles, and helper maps to optimize CPU execution.
    """
    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> np.ndarray:
        return self.cache.get(key)

    def set(self, key: str, value: np.ndarray) -> None:
        self.cache[key] = value

    def clear(self) -> None:
        self.cache.clear()
