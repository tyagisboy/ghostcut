# 09 — Edge Intelligence Runtime

## Purpose and output

Produce a full-resolution, calibrated per-pixel edge-policy map: `hard`, `fabric`, `cluster`, `strand`, `transparent`, `motion_soft`, or `unknown`. It is based on observed boundary behaviour and constrained by validated region beliefs.

## Features and policy

Use alpha transition width, source/alpha gradient alignment, structure-tensor orientation, contour curvature, local texture, and transparency evidence. Hard edges use narrow radius/edge locking; strands preserve low alpha without generic sharpening; transparency avoids threshold clamps; unknown uses conservative no-expansion policy.

## Safety/testing

Prevent strand/transparent policies inside protected skin without supporting evidence. Validate shape coverage and seam continuity. Benchmark boundary F-score, alpha transition distributions, false strand policy on grass/branches, and CPU cost by ROI.
