# 05 — Data Model Specification

## Artifact contract

All artifacts include `artifact_id`, producer runtime/version, coordinate space, dimensions, dtype/range, policy version, and parent artifact IDs. Arrays are stored in memory during a job and may be serialized as compressed sidecars; JSON stores metadata and references, not unbounded pixel data.

```python
@dataclass(frozen=True)
class Finding:
    finding_id: str
    kind: Literal['halo_light','halo_dark','halo_chroma','alpha_overexpand',
                  'alpha_erode','jagged_edge','strand_loss','region_hole',
                  'color_spill','transition_mismatch','low_confidence']
    roi: Rect
    severity: float
    confidence: float
    evidence_ids: tuple[str, ...]
    recommendation: str | None

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    runtime_id: str
    measurement: dict[str, float | str]
    calibration_version: str
    confidence: float

@dataclass(frozen=True)
class RepairRecord:
    repair_id: str
    roi: Rect
    operator: str
    parameters: dict[str, float | str]
    accepted: bool
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    rollback_artifact_id: str
```

## Quality report

`QualityReport` is immutable after export and contains score components, findings, protected regions, accepted/rejected repairs, deferred verification, policy versions, and export decision: `accept`, `warn`, or `fallback`.

## Policy maps

`RegionPolicy` contains full-resolution maps or ROI tiles for `alpha_mode`, `radius_px`, `decontamination_strength`, `sharpening_strength`, `protection_weight`, and absolute expansion/contraction caps. It must declare interpolation and seam-blending rules.

## Validation

Reject nonfinite data, mismatched image shapes, unrecognized enum values, alpha beyond `[0,1]`, confidence outside `[0,1]`, invalid rectangles, missing color space, or repair records without both before/after measurements. Source paths and personal metadata are excluded from default diagnostic serialization.

## Schema evolution

Each JSON has `schema_version`; readers support explicit migrations. Adding a field is backward-compatible only with a documented default. Removing/renaming fields requires migration and fixture updates. Do not infer missing semantic values as positive.
