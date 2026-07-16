# GhostCut Cognitive Architecture Specification v5.0

## Vision

GhostCut v5.0 transforms the application from an adaptive
image-processing pipeline into a **Cognitive Vision System**. Every
runtime becomes a sensor that contributes evidence. Decisions are made
through reasoning rather than isolated heuristics.

------------------------------------------------------------------------

# Core Cognitive Architecture

    Image
     ↓
    Vision Intelligence
     ↓
    Evidence Graph
     ↓
    Belief Graph
     ↓
    Consensus Engine
     ↓
    Strategy Engine
     ↓
    Runtime Scheduler
     ↓
    Segmentation & Refinement
     ↓
    Quality Intelligence
     ↓
    Self-Critic Engine
     ↓
    Targeted Local Repair
     ↓
    Export

------------------------------------------------------------------------

# 1. Evidence Graph

## Purpose

Standardize how every runtime reports observations.

Every runtime must output an **EvidenceNode** rather than raw values.

## EvidenceNode Schema

-   Runtime ID
-   Observation
-   Confidence
-   Supporting Features
-   Spatial Region
-   Dependencies
-   Cost
-   Timestamp
-   Explainability Notes

Example:

``` json
{
  "runtime":"HairRuntime",
  "observation":"CurlyHair",
  "confidence":0.91,
  "evidence":[
    "parallel strand density",
    "curl entropy",
    "high-frequency edges"
  ]
}
```

## Responsibilities

-   Collect observations
-   Preserve provenance
-   Enable traceability
-   Feed the Belief Graph

------------------------------------------------------------------------

# 2. Belief Graph

## Purpose

Convert observations into validated beliefs.

Beliefs may be:

-   Accepted
-   Rejected
-   Deferred
-   Competing

Each BeliefNode contains:

-   Semantic Entity
-   Supporting Evidence
-   Contradicting Evidence
-   Confidence
-   Parent/Child Relationships
-   Region References

Example

    Human
     ├── Face
     ├── Hair
     └── Clothing

The graph becomes the canonical representation of image understanding.

------------------------------------------------------------------------

# 3. Consensus Engine

## Purpose

Resolve conflicting evidence before any recipe is generated.

Inputs

-   Evidence Graph
-   Belief Graph
-   Runtime Reliability
-   Historical Learning

Operations

-   Agreement scoring
-   Contradiction detection
-   Confidence calibration
-   Rule validation
-   Historical weighting

Example Rules

-   Human + Fur → Reject Fur unless strong supporting evidence exists.
-   Plant + Skin → Reject Skin.
-   Product + Hair → Reject Hair.
-   Glass requires transparency evidence.
-   Whiskers require animal evidence.

Outputs

-   Validated Beliefs
-   Rejected Beliefs
-   Deferred Beliefs
-   Consensus Score

------------------------------------------------------------------------

# 4. Strategy Engine

## Purpose

Generate execution strategies instead of fixed recipes.

A Strategy contains:

-   Active runtimes
-   Runtime order
-   Region priorities
-   Refinement policies
-   Hardware profile
-   Repair budget
-   Export profile

Example

Portrait Strategy

-   Enable Hair Runtime
-   Enable Face Runtime
-   Disable Fur Runtime
-   High priority on facial edges
-   Preserve hair transparency

Product Strategy

-   Enable Geometry Runtime
-   Enable Reflection Runtime
-   Disable Hair Runtime
-   Maximize hard-edge precision

Strategies are dynamic and explainable.

------------------------------------------------------------------------

# 5. Self-Critic Engine

## Purpose

Evaluate GhostCut's own output before export.

Inputs

-   Output Image
-   Alpha Matte
-   Quality Reports
-   Strategy
-   Belief Graph

Checks

-   Halo artifacts
-   Missing strands
-   Broken masks
-   Color spill
-   Edge continuity
-   Transparency consistency
-   Semantic consistency

Outputs

-   Quality Grade
-   Failure List
-   Repair Regions
-   Repair Priority

Only defective regions are scheduled for local repair.

------------------------------------------------------------------------

# Cognitive Data Flow

Runtime → EvidenceNode → Evidence Graph → Belief Graph → Consensus
Engine → Strategy → Scheduler → Processing → Self-Critic → Local Repair

------------------------------------------------------------------------

# Runtime Contract v5

Every runtime must implement:

-   observe()
-   produceEvidence()
-   estimateConfidence()
-   estimateCost()
-   explain()
-   validateDependencies()

No runtime modifies decisions directly.

------------------------------------------------------------------------

# Explainability Requirements

Every decision must answer:

-   What was observed?
-   Which runtime observed it?
-   What evidence supports it?
-   What contradicted it?
-   Why was it accepted or rejected?
-   How did it influence strategy?

------------------------------------------------------------------------

# Learning Integration

Adaptive Learning updates:

-   Runtime reliability
-   Consensus weights
-   Strategy preferences
-   Repair success rates

It must never directly overwrite model outputs.

------------------------------------------------------------------------

# Success Metrics

-   Reduced contradictory classifications
-   Fewer unnecessary runtimes
-   Lower CPU usage
-   Higher strategy accuracy
-   Reduced halos
-   Better hair/fur preservation
-   Explainable reasoning
-   Stable regression performance

------------------------------------------------------------------------

# Long-Term Vision

GhostCut becomes an offline Cognitive Vision Platform.

Layers:

1.  Vision Intelligence
2.  Quality Intelligence
3.  Adaptive Learning
4.  Cognitive Reasoning
5.  Execution
6.  Self-Critic
7.  Continuous Improvement

Background removal becomes one application built on top of a reusable
cognitive vision architecture capable of supporting future features such
as smart masking, selective editing, relighting, product enhancement,
and semantic image understanding.
