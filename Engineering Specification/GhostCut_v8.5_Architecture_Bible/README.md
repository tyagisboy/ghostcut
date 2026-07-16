# GhostCut v8.5 Architecture Bible — Production Quality Intelligence

## Purpose

This bundle specifies the production-quality layer that sits after GhostCut's cognitive strategy selection and before export. Its job is to turn a strategy into a defensible alpha matte: clean hard boundaries on skin and products, continuous alpha around hair/fur/translucency, and localized repairs only where evidence shows a defect.

It does **not** introduce a new segmentation model or let quality modules silently override validated semantic beliefs. All thresholds are policies, benchmark-calibrated and versioned.

## Reading and implementation order

1. Read `01_System_Architecture.md`, `05_Data_Model_Specification.md`, and `03_Runtime_API_Specification.md` first.
2. Implement `06_Execution_Pipeline.md` and the runtime interfaces.
3. Implement quality, halo, edge, hair, material, and repair runtimes in documents 07–12.
4. Build observability/UI and the benchmark gate from documents 13–15.
5. Use diagrams and extension rules in documents 16–18 for review and future work.

## Non-negotiable invariants

- Keep the original RGB image immutable; derived images are explicit artifacts.
- A quality analyzer reports defects; only an approved repair executor changes pixels.
- Repairs are ROI-scoped, bounded, reversible, logged, and re-verified once.
- Any quality/performance change must pass the benchmark gate in document 15.
- “Unknown” is valid; do not invent a material or edge class to complete a profile.

## Deliverables

The bundle contains 18 standalone specifications. The intended implementation target is Python/PyQt/ONNX Runtime, but contracts are deliberately model-agnostic.
