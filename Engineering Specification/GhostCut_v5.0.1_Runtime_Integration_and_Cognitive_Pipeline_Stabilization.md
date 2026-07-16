# GhostCut v5.0.1 --- Runtime Integration & Cognitive Pipeline Stabilization

## Objective

Stabilize the integration between the legacy execution pipeline and the
v5.0 Cognitive Architecture. This release introduces **no new AI
capabilities**; it focuses entirely on interface consistency, runtime
compatibility, scheduler correctness, confidence validation, telemetry,
and end-to-end stability.

## Phase 1 --- Runtime API Unification

-   Replace direct `analyze()` calls with a unified `execute(context)`
    API.
-   Standardize a `RuntimeResult` containing observations, evidence,
    confidence, diagnostics, timings, and warnings.
-   Eliminate runtime-specific public interfaces from the pipeline.

## Phase 2 --- Cognitive Runtime Wrapper

-   Convert `CognitiveRuntimeWrapper` into a compatibility adapter.
-   Support legacy runtimes internally while exposing only
    `execute(context)`.
-   Ensure callers never distinguish between legacy and cognitive
    runtimes.

## Phase 3 --- Runtime Registry Validation

-   Validate duplicate IDs, missing registrations, dependency cycles,
    unsupported runtime types, and scheduler references.
-   Fail fast with clear diagnostics.

## Phase 4 --- Scheduler Stabilization

-   Deterministic topological execution.
-   Record executed/skipped runtimes, dependency graph, CPU savings, and
    execution trace.

## Phase 5 --- ExecutionContext

Create one immutable shared context containing: - Source image -
ImageProfile - HardwareProfile - EvidenceGraph - BeliefGraph - Scheduler
state - Runtime cache - Telemetry collector

## Phase 6 --- Confidence Consistency

Reject impossible states such as: - Hair=0% with Overall=100% - Human
with Fur=98% - Product using Hair recipes Add automatic assertions and
diagnostics.

## Phase 7 --- Scene Calibration

Improve Studio vs Outdoor classification using lighting, background
uniformity, edge density, depth cues, and dominant color statistics. Log
reasoning for every decision.

## Phase 8 --- GUI Synchronization

Display cognitive reasoning in order: 1. Observations 2. Evidence 3.
Beliefs 4. Consensus 5. Strategy 6. Self-Critic 7. Final Execution

## Phase 9 --- Runtime Telemetry

Record execution time, memory, confidence, warnings, errors, skipped
reason, dependency chain, and export them for VCP.

## Phase 10 --- Smoke Tests

Run portraits, curly hair, straight hair, pets, plants, products, glass,
jewelry, furniture, and transparent objects. Success: - No runtime
exceptions - No API mismatches - Successful segmentation/export

## Phase 11 --- Integration Tests

Verify Registry, Scheduler, EvidenceGraph, BeliefGraph, Consensus,
Strategy, Self-Critic, Segmentation, GUI, and Telemetry together.

## Deliverables

-   Unified Runtime API
-   RuntimeResult
-   Stable CognitiveRuntimeWrapper
-   Validated Runtime Registry
-   Deterministic Scheduler
-   ExecutionContext
-   Confidence Validator
-   Scene Calibration
-   GUI Synchronization
-   Runtime Telemetry
-   Smoke Test Suite
-   Integration Test Suite

## Exit Criteria

-   100% architecture tests pass
-   100% integration tests pass
-   Zero runtime interface errors
-   Zero inconsistent confidence reports
-   Stable GUI reasoning
-   Successful processing of all smoke-test images

## Expected Outcome

GhostCut gains a stable execution backbone that fully integrates the
cognitive architecture and becomes the foundation for the Validation &
Calibration Program (VCP).
