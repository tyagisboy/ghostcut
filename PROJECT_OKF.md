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

## 2. Component Directory Map (Vector Key: DirectoryMap)
The system codebase is divided into clear functional boundaries:

* **`/src/core/`**: Core mathematical, image processing, and runtime execution files.
  * **`segmentation.py`**: Entry orchestrator for segmentation jobs. Manages pre-processing, ONNX inference, color decontamination, and output assembly.
  * **`local_repair_runtime.py`**: Padded ROI repair logic (alpha contraction, smoothing, self-critic commits/rollbacks).
  * **`runtime_registry.py`**: System coordinator managing the initialization and sorting of Quality Runtimes.
* **`/src/core/perception/`**: Autonomous Perception Framework (APF). Coordinates memory, heuristics, and recipe-level configuration checks.
* **`/src/core/alpha_validation/`**: Quality assurance benchmark suite (AVBP). Contains the ground truth datasets and verification runners.
* **`/src/gui/`**: PyQt6 desktop user interface view layers.
  * **`main_window.py`**: Orchestrates state changes, multithreaded AI jobs, canvas interactions, and parameter actions.
  * **`components/canvas.py`**: Custom painter canvas handling scroll, zoom, trimap brush strokes, and overlay rendering.
  * **`components/toolbar.py`**: Settings widgets (Sliders for Radius, Contraction, Glass Mode).

---

## 3. Cognitive Quality Pipeline Flow (Vector Key: QualityPipeline)
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

### Boundary Quality Rules (v8.5.2)
* **Adaptive Contraction Policy**:
  * **Hair / Delicate Fibers (`protection == 1.0`)**: Apply a gentle 1-pixel contraction to keep flyaways intact.
  * **Hard Edges / Clothing / Skin (`protection == 0.0`)**: Apply a firm 3-pixel contraction to eliminate white halo outlines.
* **Spatial Boundary Color Decontamination**:
  * Selected area: Pixels within a spatial boundary transform (15px inside to 10px outside the mask edge).
  * Replaces original bright studio/white backdrop colors with local foreground colors using a spatial distance weight.
* **Floating Speckles Filter**:
  * Connected components with a surface area `< 0.002%` of the total canvas (usually `< 50px`) are automatically deleted.

---

## 4. Operational Constraints & Rules (Vector Key: RulesAndConstraints)
When editing this repository, the following rules are strictly enforced:

* **Code Comments**: Retain all legacy structural comments. Document any new mathematical formula or CV2 operation.
* **Thread Safety**: Never interact with PyQt6 UI widgets directly inside a background thread. Always communicate with the GUI thread using Qt Signals.
* **Paths**: Always use relative paths resolved from the codebase root directory (`Ai Project/`).
* **Memory Integrity**: All parameters, success rates, and local failure patterns must be written back to `learning_db.json` and `failure_db.json`.

---

## 5. Build, Packaging & Release Specification (Vector Key: BuildPipelines)
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

## 6. RAG Handshake Guide for Parallel AI Agents (Vector Key: AgentHandshake)
If you are an AI assistant parsing this repository:
1. **Scope Boundary**: Run all terminal commands, script executions, and edits inside the **`Ai Project/`** subdirectory.
2. **Ignored directories**: Never touch `/build/`, `/dist/`, or `.exe` files. Check `.gitignore` for exclusions.
3. **Large Model Weights**: ONNX models are stored in `Ai Project/src/models/` but are excluded from Git. If you need to pull them, run `python src/models/download_models.py`.
