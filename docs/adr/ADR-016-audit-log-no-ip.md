# ADR-016: Audit Log Design — No IP Storage

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-05-26 |
| Stage | 01-requirements (EV-002) |
| Deciders | User (product owner) |
| Context | F29 (Audit log & version history) |

## Context

EV-002 introduces an audit log (F29) to track all corpus modifications: document
creation, deletion, metadata edits, tag changes, bulk operations, and job state
transitions. The user requested tracking "when, by what IP and where" changes occur.

ADR-004 enforces **zero personal data** in the Vecinita system. IP addresses are
considered personal data under GDPR and many privacy frameworks (they can identify
individuals, especially when combined with timestamps).

## Decision

**Store only a `request_id` for correlation — no IP addresses, no user-agent strings,
no geolocation data.**

The audit log captures:
- **What** changed (event_type, entity_type, entity_id, payload with before/after diff)
- **When** it changed (created_at timestamp)
- **Correlation** (request_id — an opaque UUID generated per request, useful for
  correlating multiple audit events from a single bulk operation)

The audit log does NOT capture:
- IP address
- User-agent
- Geographic location
- Operator identity (no user accounts — F16, ADR-004)

## Alternatives Considered

| Option | Verdict | Rationale |
|--------|---------|-----------|
| Store raw IP | Rejected | Violates ADR-004 zero personal data |
| Store hashed IP (SHA-256) | Rejected | Still enables correlation attacks; hashes of IPs from known ranges are trivially reversible |
| No IP, request_id only | **Accepted** | ADR-004 compliant; sufficient for operational correlation |

## Consequences

- Operators cannot determine which network location initiated a change by querying
  Vecinita's database alone.
- If network-level audit is needed, operators should rely on their deployment platform's
  access logs (DigitalOcean App Platform logs, load balancer logs) which are outside
  Vecinita's data boundary.
- The `request_id` allows correlating multiple audit events from a single API call
  (e.g., a bulk delete that affects 50 documents generates 50 audit rows with the same
  `request_id`).

## Schema

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(64) NOT NULL,  -- document.created, document.deleted, etc.
    entity_type VARCHAR(32) NOT NULL, -- document, chunk, job
    entity_id UUID NOT NULL,
    request_id UUID NOT NULL,         -- correlation only, no identity
    payload JSONB NOT NULL DEFAULT '{}',  -- before/after diff
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title TEXT,
    language VARCHAR(8),
    tags_snapshot JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_number)
);
```

## References

- ADR-004: Zero personal data
- F16: Infrastructure-only protection
- F29: Audit log & version history (EV-002)
