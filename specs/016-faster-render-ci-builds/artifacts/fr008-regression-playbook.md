# FR-008 regression playbook (016)

Use this playbook when FR-008 monitored dimensions regress versus `post-optimization-snapshot.md`.

## Trigger

A regression review is required when any monitored metric (M1/M2 and optional M3-M5) shows sustained degradation against baseline/snapshot medians under comparable load and sample rules.

## Decision window

- Open a regression record within 2 business days of detection.
- Finalize one outcome below within **14 calendar days** of detection.

## Outcomes (record one)

1. **Re-baseline**
   - Use when environment/system behavior has materially shifted.
   - Record new sampling window, rationale, and updated target medians in governance artifacts.

2. **Revert**
   - Use when optimization changed behavior or reliability in unacceptable ways.
   - Record reverted commits/PR, affected checks/services, and restored baseline references.

3. **New target**
   - Use when current target is unattainable but safety/correctness is preserved.
   - Record revised target, approver, and rationale in governance artifacts.

## Evidence required

- Updated metric table rows (median, n_runs, cache_state, source).
- Comparable-load note (or explicit exception).
- Any branch protection or check-intent changes must include FR-004 EquivalenceRecord entries.

## Flakiness tolerance

No numeric week-over-week retry tolerance is currently set; use engineering-lead qualitative tolerance from spec edge cases until a numeric threshold is approved.
