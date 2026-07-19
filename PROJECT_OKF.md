# Open Knowledge Format (OKF) & RAG Memory Map: GhostCut Offline (v8.5.2)

This specification serves as a structured, machine-readable RAG (Retrieval-Augmented Generation) memory index. It enables parallel AI agents (Antigravity, Cursor, Claude Code, ChatGPT) to instantly build a mental model of the codebase, system dependencies, constraints, and architecture.

---

## 1. Project Schema & System Specifications
```json
{
  "project_name": "GhostCut Offline",
  "version": "8.5.2",
  "language": "Python 3.11+",
  "gui_framework": "PyQt6",
  "inference_engines": ["ONNX Runtime (GPU/CPU)", "OpenCV DNN"],
  "models": {
    "segmentation": "birefnet-general-lite.onnx",
    "matting": "vitmatte-small.onnx"
  },
  "installer_builder": "NSIS (makensis.exe)",
  "executable_packager": "PyInstaller"
}
```

---

## 2. Directory Map & Component Roles (Vector Key: DirectoryMap)

* **`/src/core/`**: Core mathematical, image processing, and runtime execution files.
  * **`segmentation.py`**: Entry orchestrator for segmentation jobs. Manages pre-processing, ONNX inference, color decontamination, and output assembly.
  * **`local_repair_runtime.py`**: Padded ROI repair logic (alpha contraction, smoothing, self-critic commits/rollbacks).
  * **`runtime_registry.py`**: System coordinator managing the initialization and sorting of Quality Runtimes.
  * **`hair_morphology_runtime.py`**: Analyzes hair characteristics to determine the matting policy.
  * **`edge_intelligence_runtime.py`**: Classifies boundary pixel zones.
  * **`material_boundary_runtime.py`**: Generates material-based protection layers.
  * **`halo_detection_runtime.py`**: Detects color bleeding and background halos.
  * **`quality_intelligence_runtime.py`**: Compliles final quality reports.
* **`/src/core/perception/`**: Autonomous Perception Framework (APF). Coordinates memory, heuristics, and recipe-level configuration checks.
  * **`perception_orchestrator.py`**: Dynamically adjusts execution based on system telemetry.
  * **`recipe_memory_runtime.py`**: Manages parameter caching and matching.
* **`/src/core/alpha_validation/`**: Quality assurance benchmark suite (AVBP). Contains the ground truth datasets and verification runners.
* **`/src/gui/`**: PyQt6 desktop user interface view layers.
  * **`main_window.py`**: Orchestrates state changes, multithreaded AI jobs, canvas interactions, and parameter actions.
  * **`components/canvas.py`**: Custom painter canvas handling scroll, zoom, trimap brush strokes, and overlay rendering.
  * **`components/toolbar.py`**: Settings widgets (Sliders for Radius, Contraction, Glass Mode).

---

## 3. Detailed Algorithmic & Mathematical Specifications (Vector Key: AlgorithmsAndMath)

### 3.1. Spatial Boundary Color Decontamination
To replace original studio backdrop colors with natural foreground color at the silhouette border:
1. **Distance Transform Calculation**:
   Given the alpha mask $A$ (scaled to $[0, 1]$), calculate distance transforms $D_{in}$ (distance inside the mask boundary) and $D_{out}$ (distance outside the mask boundary):
   $$D_{in} = \text{distanceTransform}(A \ge 0.5)$$
   $$D_{out} = \text{distanceTransform}(A < 0.5)$$
2. **Transition Zone Identification**:
   A pixel $p$ is in the decontamination transition zone if:
   $$(D_{in}(p) \le 15) \lor (D_{out}(p) \le 10)$$
3. **Local Color Sampling & Blending**:
   For each pixel $p$ in the transition zone:
   * Scan a localized neighborhood ring ($R_{search} = 7\text{px}$) inside the foreground boundary ($D_{in} > 15$) to compute the local target color $C_{fg}(p)$ via spatial distance weights.
   * Replace original pixel color $C_{orig}(p)$ with:
     $$C_{decon}(p) = C_{fg}(p)$$
   * Blend with transparency mask:
     $$C_{final}(p) = \alpha(p) \cdot C_{decon}(p) + (1 - \alpha(p)) \cdot C_{bg}(p)$$

### 3.2. Material-Guided Adaptive Mask Contraction
To trim white outlines on hard borders without degrading fine hair details:
1. **Material Map Extraction**:
   From segmentation maps, extract the hair/fur probability mask $P_{detail}$ (where $P_{detail} \in [0, 1]$).
2. **Adaptive Kernel Radius**:
   Compute the erosion kernel radius $R_{erode}(p)$ dynamically for each boundary pixel:
   $$R_{erode}(p) = \text{round}(R_{max} \cdot (1.0 - P_{detail}(p)) + R_{min} \cdot P_{detail}(p))$$
   Where $R_{max} = 3\text{px}$ (hard borders like skin/clothing) and $R_{min} = 1\text{px}$ (hair borders).
3. **Erosion Operator**:
   Apply localized erosion using a flat structuring element of radius $R_{erode}(p)$.

### 3.3. Scale-Aware Connected Component Speckle Filter
To delete background noise speckles:
1. **Size Threshold Formula**:
   Given image height $H$ and width $W$:
   $$\text{Threshold}_{min\_size} = \max\left(50, \lfloor H \cdot W \cdot 0.00002 \rfloor\right)$$
2. **Component Filtering**:
   Identify connected components on the binary mask $A_{bin} = (A > 0)$ using 8-connectivity. For each component $i$ with pixel area $\text{Area}_i$:
   $$\alpha(p) = 0 \quad \forall p \in \text{Component}_i \quad \text{if } \text{Area}_i < \text{Threshold}_{min\_size}$$

---

## 4. Cognitive Quality Pipeline Flow & Runtimes (Vector Key: QualityPipeline)
All segmentation jobs execute a 5-phase sequential quality verification loop inside `segmentation.py`:

```
[Phase 1: Validate] -> Check Input Bounds & Channels
        │
[Phase 2: Analyze]  -> Execute Edge & Hair Morphology Runtimes
        │
[Phase 3: Fuse]     -> Consolidate Material Segments (Skin, Hair, Cloth)
        │
[Phase 4: Repair]   -> Run Material-Guided Contraction (LocalRepairRuntime)
        │
[Phase 5: Verify]   -> Run Self-Critic Defect Verification
                       ├── PASS: Commit locally repaired ROI
                       └── FAIL: Rollback to pre-repaired state
```

### 4.1. Runtime Execution API Signature
Every runtime class implements the standard execution interface:
```python
class IQualityRuntime(ABC):
    @abstractmethod
    def execute(self, context: QualityContext) -> RuntimeResult:
        """
        Executes analysis or repair.
        context: Shared thread-safe dictionary holding images, masks, and metadata.
        returns: RuntimeResult containing success status and report metrics.
        """
        pass
```

### 4.2. Self-Critic Transaction & Defect Verification
Inside `LocalRepairRuntime`:
1. **Defect Pixel Definition**: A pixel $p$ is a "boundary defect" if the color difference between the foreground and background exceeds a set threshold.
2. **Defect Counting**:
   $$\text{Defects} = \sum_{p \in \text{Contour}} [\|C_{fg}(p) - C_{bg}(p)\| < \text{Threshold}_{defect\_limit}]$$
   * Bright background threshold: `120.0`
   * Dark background threshold: `60.0`
3. **Commit/Rollback Transaction**:
   * Calculate pre-repair defect count: $N_{pre}$.
   * Apply contraction, then calculate post-repair defect count: $N_{post}$.
   * Decision Logic:
     $$\text{Transaction} = \begin{cases} 
       \text{Commit} & \text{if } N_{post} < N_{pre} \\
       \text{Rollback} & \text{if } N_{post} \ge N_{pre} 
     \end{cases}$$

---

## 5. GUI State & Live Preview Sync (Vector Key: GuiStateManagement)

* **Processed State Registry (`self.processed_files`)**:
  * Tracks absolute file paths that have completed full AI segmentation at least once.
* **Auto-Apply Guard Logic**:
  * Adjusting settings (such as matting radius or threshold sliders) triggers a live preview update *only* if the file path is present in `self.processed_files`.
  * For freshly loaded, unprocessed files, settings are saved locally in the UI state config without triggering background operations, keeping GUI resource consumption low.
* **Slider Boundary Range**:
  * Slider ranges for edge erosion/dilation limits are set to `(1, 25)px` in `toolbar.py` to allow tight `1px` detail extraction.

---

## 6. Build, Packaging & Release Specification (Vector Key: BuildPipelines)
To package the codebase into a standalone windows executable:

1. **Step 1 (Compile)**: Run PyInstaller from `Ai Project/` directory:
   ```powershell
   & "C:\Users\Neha Tyagi\AppData\Local\Python\pythoncore-3.14-64\Scripts\pyinstaller.exe" --noconfirm --clean build_scripts/pyinstaller_win.spec
   ```
   * *Output*: Bundled folder created at `Ai Project/dist/GhostCutOffline/`.
2. **Step 2 (Package)**: Run NSIS Compiler from `Ai Project/build_scripts/` directory:
   ```powershell
   & "C:\Users\Neha Tyagi\AppData\Local\electron-builder\Cache\nsis\nsis-3.0.4.1\makensis.exe" installer_config.nsi
   ```
   * *Output*: Standalone installer `GhostCut_Offline_Setup_v1.0.0.exe` written to `Ai Project/build_scripts/`.
3. **Step 3 (Deliver)**: Copy the installer to the delivery directory:
   ```powershell
   Copy-Item -Path "Ai Project/build_scripts/GhostCut_Offline_Setup_v1.0.0.exe" -Destination "Distribution/GhostCut_Offline_Setup_v1.0.0.exe" -Force
   ```

---

## 7. RAG Handshake Guide for Parallel AI Agents (Vector Key: AgentHandshake)
If you are an AI assistant parsing this repository:
1. **Scope Boundary**: Run all terminal commands, script executions, and edits inside the **`Ai Project/`** subdirectory.
2. **Ignored directories**: Never touch `/build/`, `/dist/`, or `.exe` files. Check `.gitignore` for exclusions.
3. **Large Model Weights**: ONNX models are stored in `Ai Project/src/models/` but are excluded from Git. If you need to pull them, run `python src/models/download_models.py`.
