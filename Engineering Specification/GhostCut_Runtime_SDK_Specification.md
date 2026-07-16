# GhostCut Runtime SDK Specification (v2)

This specification defines the SDK contracts, lifecycle APIs, and data transfer formats for modular intelligence runtimes.

---

## 1. Modular Runtime Interface Contract

Every intelligence analyzer component MUST implement the standard runtime lifecycle methods.

```python
class IGhostCutRuntime:
    """
    Standard base interface governing all GhostCut intelligence runtimes.
    """
    def initialize(self, config: dict) -> None:
        """
        Setup cache sessions, load parameter files, or prime ONNX providers.
        """
        pass
        
    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray, features: dict) -> dict:
        """
        Executes analysis on the input image BGR matrix and optional mask.
        Returns a dictionary containing analyzer output attributes.
        """
        raise NotImplementedError
        
    def validate(self) -> list:
        """
        Runs self-diagnostics. Returns list of warning/error strings if invalid.
        """
        return []
```

---

## 2. Specific Module SDK Contracts

### A. Scene Intelligence Runtime (`scene.py`)
- **Responsibilities**: Detects pre-inference scene profile category.
- **Inputs**: `img_bgr` (BGR numpy matrix).
- **Outputs**: `{"scene": str, "confidence": float}`.
- **Performance Targets**: `< 5ms` execution time.

### B. Subject Intelligence Runtime (`subject.py`)
- **Responsibilities**: Identifies presence of multiple simultaneous subjects.
- **Inputs**: `img_bgr` (BGR numpy matrix), `raw_mask` (from fast segmentation).
- **Outputs**: `{"subjects": list[str], "confidence": dict[str, float]}`.
- **Performance Targets**: `< 2ms`.

### C. Background Intelligence Runtime (`background.py`)
- **Responsibilities**: Measures background complexity, contrast, blur, and gradients.
- **Inputs**: `img_bgr` (BGR numpy matrix), `raw_mask` (optional).
- **Outputs**: `{"complexity": str, "blur": float, "separation_difficulty": float}`.
- **Performance Targets**: `< 3ms`.

### D. Subject Region Graph Runtime (`region_graph.py`)
- **Responsibilities**: Constructs the logical adjacency graph of segments.
- **Inputs**: `img_bgr`, `mask`, `material_maps`.
- **Outputs**: `{"nodes": list[dict], "edges": list[tuple]}`.
- **Performance Targets**: `< 10ms`.

### E. Material Runtime (`material_runtime.py`)
- **Responsibilities**: Generates pixel-level material maps (Skin, Hair, Fur, etc.).
- **Inputs**: `img_bgr`, `mask`.
- **Outputs**: `{"maps": np.ndarray (H, W, 10), "scores": dict[str, float]}`.
- **Performance Targets**: `< 15ms`.

### F. Hair Runtime (`hair_runtime.py`) & Fur Runtime (`fur_runtime.py`)
- **Responsibilities**: Computes structural attributes of hair/fur.
- **Inputs**: `img_bgr`, `mask`, `w_detail`.
- **Outputs**: `{"hair_type": str, "density": float}`, `{"fur_type": str, "whiskers": bool}`.
- **Performance Targets**: `< 5ms`.

### G. Edge Runtime (`edge_runtime.py`)
- **Responsibilities**: Classifies edge zones into distinct type classes.
- **Inputs**: `img_bgr`, `mask`, `material_maps`.
- **Outputs**: `{"edge_map": np.ndarray (H, W), "classes": list[str]}`.
- **Performance Targets**: `< 10ms`.

### H. Regional Recipe Engine (`regional_recipe.py`)
- **Responsibilities**: Compiles customized recipe parameters per node of the Subject Region Graph.
- **Inputs**: `ImageProfile`, `SubjectRegionGraph`.
- **Outputs**: `{"regions": dict[str, dict]}` where values are parameter dicts.
- **Performance Targets**: `< 1ms`.
