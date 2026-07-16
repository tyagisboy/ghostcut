# 17 — Class Diagrams

```mermaid
classDiagram
 class ExecutionContext {+artifacts +strategy +policy +budget}
 class BaseRuntime {+execute(context) RuntimeResult}
 class RuntimeResult {+status +findings +evidence +telemetry}
 class QualityReport {+findings +score +repairs +decision}
 class RepairProposal {+roi +operator +limits +expected_gain}
 class RepairRecord {+accepted +before +after +rollback}
 BaseRuntime <|-- QualityIntelligenceRuntime
 BaseRuntime <|-- LocalRepairRuntime
 ExecutionContext --> RuntimeResult
 RuntimeResult --> QualityReport
 QualityReport --> RepairProposal
 RepairProposal --> RepairRecord
```

Context owns job-lifetime artifact references; application owns immutable source lifetime; reports are immutable after export; repair records are append-only. Runtime instances cannot retain job arrays except explicit bounded caches.
