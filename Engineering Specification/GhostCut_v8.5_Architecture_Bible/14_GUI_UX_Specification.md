# 14 — GUI/UX Specification

## Standard workspace

The canvas and export controls remain primary. A compact Quality card presents at most three useful outcomes, status, and processing time; it does not present a scrolling cognitive log.

```text
Files | Original / Result canvas | Quality: High
      |                          | ✓ Fine edges preserved
      |                          | ✓ Edge spill corrected
      |                          | [Details] [Export]
```

## Professional workspace

`Details` opens dockable Quality, Repairs, Edge Overlay, Timeline, and Diagnostics panels. Selecting a repair highlights its ROI, shows before/after metrics, and permits disable-before-export. Debug trace is an explicit developer-only toggle. During work, show meaningful stages/progress; after work, show result and any unresolved warning.

## Accessibility/validation

All status text has accessible labels, overlays have non-colour cues, and no user action is blocked by an unexplained confidence score. Test standard mode with no technical vocabulary and professional mode with trace-to-ROI navigation.
