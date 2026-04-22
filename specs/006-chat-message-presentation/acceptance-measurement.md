# Acceptance Measurement Protocol (SC-002, SC-004)

## Scope

Define a repeatable lightweight validation protocol for:

- **SC-002**: Sender identification speed/accuracy
- **SC-004**: Perceived assistant readability improvement

## Participants

- Minimum 10 participants representing typical end users.
- Mixed desktop/mobile browser usage where feasible.

## Procedure

1. Present a mixed conversation screenshot or live thread with alternating user/assistant messages.
2. Ask participant to identify sender of 5 highlighted messages; measure response latency per item.
3. Run short task where participant reads one assistant reply in old format and one in new format.
4. Collect readability rating (Likert 1-5) and preference note.

## Success Thresholds

- **SC-002 pass**: >=90% of participants identify sender correctly within 2 seconds median per prompt.
- **SC-004 pass**: >=90% of participants rate new assistant formatting as improved over prior presentation.

## Evidence Capture

- Store raw timing and survey responses in test execution artifacts for implementation review.
