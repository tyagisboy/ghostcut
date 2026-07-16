# 03 — Runtime API Specification

## Stable contract

All runtimes expose `execute(context) -> RuntimeResult`; callers must not use private methods such as `analyze()`. Context is job-scoped and read-only except for the dedicated repair transaction API.

```python
class BaseRuntime(Protocol):
    runtime_id: str
    dependencies: tuple[str, ...]
    def execute(self, context: ExecutionContext) -> RuntimeResult: ...

@dataclass(frozen=True)
class RuntimeResult:
    status: Literal['ok','skipped','failed']
    findings: tuple[Finding, ...]
    evidence: tuple[Evidence, ...]
    artifacts: Mapping[str, ArtifactRef]
    telemetry: RuntimeTelemetry
    warnings: tuple[str, ...]
```

## Context and artifacts

`ExecutionContext` supplies immutable source image, alpha artifacts, validated beliefs/strategy, regional policy, hardware budget, cancellation signal, and namespaced dependency results. Every array artifact declares shape, dtype, range, color space, and coordinate frame. Alpha is float32 `[0,1]`; no implicit BGR/RGB conversion is permitted.

## Repair transaction API

Only `LocalRepairRuntime` may stage `candidate_alpha` through `context.repairs.stage()`. Stage requires ROI, operator, parameters, parent artifact, protected mask, and expected metric. `commit()` is legal only after verifier acceptance; `rollback()` is mandatory on failure/cancellation.

## Error and compatibility rules

Required invalid input returns `failed`; optional unavailable work returns `skipped` with reason. Never return malformed output as `ok`. Runtime and schema versions are checked by registry startup validation. New fields are additive with explicit defaults; incompatible changes require migrations and fixture updates.

## Contract tests

Test shape/range validation, deterministic output, cancellation, missing dependency behavior, telemetry emission, registry wrappers, and rollback with no mutation outside the padded ROI.
