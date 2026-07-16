# GhostCut Next: Image Intelligence Engine Implementation Plan

This plan details the transition of GhostCut from a linear background removal pipeline into an adaptive **Image Intelligence Engine**. The engine will analyze each image dynamically prior to inference, generate a customized processing recipe, map local materials and edges, and run optimized local repairs guided by confidence maps.

## User Review Required

Please review the following core architecture and design details:

> [!IMPORTANT]
> **Performance Optimization Strategy:**
> To ensure CPU-first compatibility and zero external API dependencies, all pre-inference classifications (Scenario, Material, Edge, and Confidence maps) are designed using optimized NumPy and OpenCV vector operations. This ensures pre-processing overhead remains below **10-50ms** per image.

> [!IMPORTANT]
> **Confidence-Driven Local Repair:**
> We are upgrading the existing block-based quality check into a continuous **Confidence-Driven Local Repair Engine**. Instead of checking only generic categories, the engine will use specialized confidence metrics to target local crops for heavy/high-precision inference (e.g., ViTMatte) and blend them back seamlessly, saving massive CPU cycles by avoiding full-scale model runs.

> [!WARNING]
> **Policy Hierarchy Overrides:**
> Policy configurations (Priority 9) will follow a strict inheritance model:
> `Global Settings` → `Hardware Constraints` → `Scenario Defaults` → `User Preference Overrides`.
> If DirectML/CUDA is unavailable, the recipe engine will automatically downscale ViTMatte scale factors or switch to Fast Guided Matting.

## Proposed Changes

We will group changes into three main components: Core Image Intelligence, Adaptive Pipeline Execution, and Explainable UX.

---

### Component 1: Image Intelligence Modules

This component covers the pre-inference classifiers, material classifiers, edge classifiers, and confidence engines.

#### [NEW] [recipe.py](file:///h:/AI%20Tools/Background%20Removal/src/core/recipe.py)
Defines the `ProcessingRecipe` schema and the `RecipeEngine` that compiles hardware settings and pre-inference image profiles into executable recipes.
- Selects the segmentation model (`birefnet-general` vs `birefnet-general-lite`).
- Configures matting mode (`fast` vs `quality` vs `ultra`).
- Defines target trimap, radius fields, and decontamination flags.

#### [NEW] [scenario.py](file:///h:/AI%20Tools/Background%20Removal/src/core/scenario.py)
Implements the `ScenarioClassifier` to detect high-level scenarios (`Studio Portrait`, `Product`, `Pet`, `Glass`, `Clothing`, etc.) on a downscaled image (e.g. 256x256) prior to running segmentation.
- Computes spatial descriptors, dynamic range, and color histograms.
- Activates dedicated scenario policies.

#### [NEW] [material.py](file:///h:/AI%20Tools/Background%20Removal/src/core/material.py)
Implements the `MaterialClassifier` producing pixel-wise probability maps and confidence scores for materials: `Skin`, `Hair`, `Fur`, `Fabric`, `Glass`, `Plastic`, `Metal`, `Leather`, `Feather`, `Lace`, `Water`, `Smoke`.

#### [NEW] [edge.py](file:///h:/AI%20Tools/Background%20Removal/src/core/edge.py)
Implements `EdgeClassifier` classifying boundaries into classes: `Hard`, `Soft`, `Hair`, `Fur`, `Fabric`, `Transparent`, `Reflection`, `Motion Blur`, `Shadow`, `Whisker`.

#### [NEW] [radius.py](file:///h:/AI%20Tools/Background%20Removal/src/core/radius.py)
Implements the `AdaptiveRadiusFieldGenerator` generating a custom radius map for Guided Filter / Matting inputs based on local material and edge classes (e.g. blending Hair 12px, Skin 2px, Glass 8px, Whiskers 15px).

#### [NEW] [confidence.py](file:///h:/AI%20Tools/Background%20Removal/src/core/confidence.py)
Implements `ConfidenceEngine` generating confidence maps (Segmentation, Hair, Fur, Material, Edge, Transparency, Alpha).

#### [NEW] [policies.py](file:///h:/AI%20Tools/Background%20Removal/src/core/policies.py)
Centralizes policy-based configurations for scenarios, materials, and edges, allowing users/developers to tune parameters globally or per-image-class.

---

### Component 2: Pipeline Integration & Diagnostics

This component covers pipeline orchestration, runtime validation, synthetic profiling, explainable logging, and interactive testing.

#### [NEW] [explain.py](file:///h:/AI%20Tools/Background%20Removal/src/core/explain.py)
Implements explainable decision logging (`DecisionLogger`). Automatically records input properties, decision criteria, parameter selections, and warnings in structured JSON logs.

#### [NEW] [validation.py](file:///h:/AI%20Tools/Background%20Removal/src/core/validation.py)
Implements runtime pipeline integrity validator to check GPU/CPU configurations, model file presence, memory footprints, and parameters before starting execution.

#### [NEW] [synthetic.py](file:///h:/AI%20Tools/Background%20Removal/src/core/synthetic.py)
Generates virtual image profiles (subject, background complexity, lighting) and verifies that the `RecipeEngine` produces the expected recipe configuration without running actual AI inference.

#### [NEW] [arch_test.py](file:///h:/AI%20Tools/Background%20Removal/src/core/arch_test.py)
Integrates a rule-based and property-based test framework checking configuration constraints, pipeline graphs, and regression behaviors.

#### [MODIFY] [segmentation.py](file:///h:/AI%20Tools/Background%20Removal/src/core/segmentation.py)
Integrates the new Image Intelligence Engine:
- Before running the core ONNX models, run the pre-inference classifiers to generate the `ProcessingRecipe`.
- Run the segmentation engine using parameters dictated by the recipe.
- During matting, apply the adaptive radius field and region-based alpha policies.

#### [MODIFY] [quality.py](file:///h:/AI%20Tools/Background%20Removal/src/core/quality.py)
Upgrades the local repair logic to run a continuous **Confidence-Driven Local Repair Engine**:
- Analyzes the initial output mask using the Confidence Engine.
- Groups low-confidence regions into tight bounding boxes.
- Runs high-precision crop-based matting (ViTMatte or multi-scale scale fusion) and blends it back using feathered distance masks.

#### [MODIFY] [batch_improve_suite.py](file:///h:/AI%20Tools/Background%20Removal/src/core/batch_improve_suite.py)
Updates the batch processing test script to evaluate performance and quality using the new pipeline, comparing baseline runtimes vs. the recipe-based runtime.

---

### Component 3: GUI Dashboard Integration

#### [MODIFY] [main_window.py](file:///h:/AI%20Tools/Background%20Removal/src/gui/main_window.py)
Updates the PyQt6 main interface to support the new Image Intelligence dashboard features:
- Display the computed scenario, active policies, and explainability decision log inside a modern side dock.
- Highlight low-confidence regions visually on the canvas (toggleable overlay).
- Show runtime validation status and hardware utilization.

#### [MODIFY] [sidebar.py](file:///h:/AI%20Tools/Background%20Removal/src/gui/components/sidebar.py)
Adds visual widgets displaying:
- Detected Scenario & Core Materials.
- The compiled `ProcessingRecipe`.
- Hardware Status & Execution Times.

---

## Verification Plan

### Automated Tests
We will execute the architecture test framework and the synthetic profiling validations:
1. Run the architecture rules verification:
   ```bash
   & "C:\Users\Neha Tyagi\AppData\Local\Python\bin\python.exe" src/core/arch_test.py
   ```
2. Run the synthetic profile checks:
   ```bash
   & "C:\Users\Neha Tyagi\AppData\Local\Python\bin\python.exe" src/core/synthetic.py
   ```
3. Run the batch improvement suite to verify real-image processing across different categories (Portrait, Product, Glass, Pet):
   ```bash
   & "C:\Users\Neha Tyagi\AppData\Local\Python\bin\python.exe" src/core/batch_improve_suite.py
   ```

### Manual Verification
1. Launch the updated application:
   ```bash
   & "C:\Users\Neha Tyagi\AppData\Local\Python\bin\python.exe" src/main.py
   ```
2. Load various test images (`test_curly1.jpg`, `test_curly2.jpg`, `test_curly4.jpg`, and other product/transparent files in `Test images`).
3. Verify that the UI sidebar renders the explainability log and shows the generated processing recipe.
4. Verify that local repairs run on low-confidence regions, producing high-fidelity output.
