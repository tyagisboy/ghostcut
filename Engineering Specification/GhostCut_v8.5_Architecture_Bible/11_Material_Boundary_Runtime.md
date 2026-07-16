# 11 — Material Boundary Runtime

## Purpose

This runtime turns validated regional material beliefs and measured edge behavior into **conservative boundary policies**. It does not identify arbitrary materials from a whole image and must never force a material label because a policy requires one. Its function is to answer: what alpha behavior is safest at this boundary—hard/opaque, fabric-like, strand-like, translucent, reflective, or unknown?

## Inputs and output

Inputs: source RGB, initial alpha, validated region graph, edge-intelligence output, transparency belief, protected masks, and policy version. Output: `MaterialBoundaryResult` with boundary evidence, material confidence, policy tile, and conflicts for consensus.

```python
@dataclass(frozen=True)
class MaterialBoundaryResult:
    roi: Rect
    boundary_mode: Literal['hard_opaque','fabric','strand','translucent','reflective','unknown']
    material_beliefs: dict[str, float]
    transparency_confidence: float
    protection_weight: float
    policy: RegionPolicy
    conflicts: tuple[str, ...]
    evidence: tuple[Evidence, ...]
```

## Processing sequence

1. Build boundary ROIs from the region graph; do not classify the background as a subject material.
2. Gather upstream validated beliefs. Suppress impossible/unvalidated material categories rather than treating them as weak positives.
3. Measure local alpha width, gradient alignment, specular/color variation, foreground/background separation, and texture continuity.
4. Fuse evidence with calibrated prior reliability. If disagreement is high, emit `unknown`.
5. Compile a policy tile bounded by global safety limits and protected masks.

## Boundary policies

| Mode | Alpha handling | Decontamination | Safety limit |
|---|---|---|---|
| hard_opaque (skin/product) | narrow transition, edge lock | minimal | no expansion beyond small cap |
| fabric | moderate continuous transition | low/medium | preserve folds, avoid holes |
| strand | delegate to Hair/Fur morphology | confidence-weighted | no unverified strand synthesis |
| translucent (glass/lace) | preserve gradients | very conservative | never hard-threshold |
| reflective | retain contour; avoid colour overcorrection | minimal | reflection alone is not transparency |
| unknown | conservative baseline | off/low | no expansion and no aggressive sharpening |

## Material-specific guardrails

- **Skin:** protection comes from region confidence and face/skin boundaries, not simply a warm color heuristic.
- **Glass/translucency:** require both semantic plausibility and local alpha/color evidence; reflections do not prove transparency.
- **Metal:** preserve hard contour but do not classify highlight as background leak.
- **Fabric/lace:** allow gradual alpha only where source texture and validated region support it.
- **Hair/fur:** defer morphology parameters to their specialized runtimes.

## Conflict and failure handling

If material suggests translucent but edge analyzer reports a confident hard opaque edge, emit conflict and choose `unknown` or the less destructive policy. Missing candidate material/region data returns `SKIPPED`; invalid artifact data returns `FAILED`; neither should create a fallback material guess.

## Tests and benchmarks

Unit-test all policy bounds, conflict resolution, and unknown fallback. Benchmark hard products, skin/hair boundaries, white fabric against pale backgrounds, glass against clutter, metal highlights, lace, and adversarial grass/branches. Gate changes on hard-edge F-score, transparency preservation, halo metrics, and false-transparency rate.
