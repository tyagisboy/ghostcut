# 16 — Sequence Diagrams

```mermaid
sequenceDiagram
 participant Sch as Scheduler
 participant Ana as Analyzers
 participant Q as Quality
 participant Rep as Repair
 participant Ver as Verifier
 Sch->>Ana: initial alpha + policies + ROI budget
 Ana-->>Q: findings/evidence/telemetry
 Q-->>Rep: approved proposal or no-op
 alt repair approved
   Rep->>Ver: candidate + rollback token
   Ver-->>Rep: accept or rollback
 end
 Rep-->>Sch: FinalMattePackage + provenance
```

Cancellation is cooperative: analyzers return partial read-only results; repair never commits without verification. Verification reruns only analyzers affected by the proposed operator and allows one ROI-local retry.
