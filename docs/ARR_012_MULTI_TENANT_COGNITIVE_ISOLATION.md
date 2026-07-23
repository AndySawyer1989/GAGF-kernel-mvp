# ARR-012 Multi-Tenant Cognitive Isolation

## Status

- Story range: ARR-012-001 through ARR-012-023
- Implementation status: Proven end to end
- Authoritative regression state at documentation start: 3,073 tests passed
- Security posture: Fail closed
- Isolation unit: Tenant
- Decision authority: Deterministic GAGF constitutional services

## Purpose

ARR-012 establishes multi-tenant cognitive isolation across the scientific authority, evidence, artifact, response, and audit layers.

Tenant isolation is enforced through identity propagation, namespace derivation, tenant-bound lookup, public projection, runtime response auditing, immutable evidence recording, and end-to-end isolation tests.

## Core Isolation Invariant

For any tenants A and B, where A is not B:

> No request authenticated in Tenant A may resolve, retrieve, infer, enumerate, or receive an artifact, identity context, audit record, namespace binding, cursor, or canonical identifier belonging exclusively to Tenant B.

Identical evidence does not authorize shared public identity.

## Identity Binding

A governed request binds tenant_id, actor_id, credential_id, session_id, role_id, policy_scope, request_id, and correlation_id.

Internal actor, credential, session, request, and correlation identifiers must not appear in tenant-facing responses.

## Zero Trust Authorization

Required controls include:

- Credential verification
- Session verification
- Device trust
- Tenant-membership verification
- Role permission
- Policy-scope permission
- Tenant-context agreement

Authorization occurs before protected artifact resolution.

## Canonical and Public Identifier Separation

Canonical identifiers are internal constitutional evidence.

Tenant clients operate through namespaced public identifiers.

Public identifiers are tenant-bound, deterministic, distinct across tenants, and resolvable only inside the owning tenant.

## Tenant Namespace

The namespace layer maps tenant-public identifiers to canonical internal artifacts.

Cross-tenant public identifier resolution returns not found rather than revealing whether another tenant owns the identifier.

## Public Response Projection

Tenant-facing APIs do not serialize internal domain objects directly.

Public projectors remove canonical identifiers, internal hashes, identity context, trust signals, and internal authorization receipts.

## Runtime Public-Boundary Enforcement

Every governed tenant response passes through the public-boundary auditor before release.

Fail-closed behavior applies to all boundary failures.

A failed boundary audit must never return the rejected payload.

## Boundary Audit Evidence Ledger

Every response decision is recorded in an append-only SQLite ledger.

The ledger uses a deterministic hash chain beginning with a fixed genesis hash.

An invalid audit cannot be recorded as released.

Rejected secret values are not stored in release evidence.

## Tenant-Scoped Audit Evidence

Tenants may inspect only their own boundary-enforcement history.

Tenant-visible evidence uses Tenant-local sequence numbers and public record identifiers.

A tenant cannot resolve another tenant's public audit-record identifier.

Global sequence numbers and internal ledger hashes remain hidden from tenant query results.

## Bounded Pagination

Audit queries use a default page size, maximum page size, tenant-bound cursor, Snapshot sequence, and tenant-local ordering.

The initial snapshot excludes audit-access records created after pagination begins.

This prevents recursive audit logging from creating non-terminating pagination.

## Shared Application Registration

Both tenant routers use the central tenant application router registry.

The authority API and audit-query API share one authoritative boundary-audit database path.

## End-to-End Isolation Proof

The integrated application proves that identical cross-tenant evidence produces distinct public identifiers, tenants retrieve only their own artifacts, foreign access returns 404, and public responses pass boundary re-audit.

## Threat Model

### Threat: Direct Cross-Tenant Artifact Access

Mitigation: authorization before resolution, tenant-bound namespace lookup, and 404 responses.

### Threat: Identical Input Collision

Mitigation: tenant identity participates in public identifier derivation.

### Threat: Canonical Identifier Leakage

Mitigation: public projection, exact hash allowlists, recursive response auditing, and fail-closed release.

### Threat: Authorization Context Leakage

Mitigation: identity-context redaction and forbidden-key auditing.

### Threat: Audit Ledger Enumeration

Mitigation: tenant-local sequence numbers and tenant-safe public record identifiers.

### Threat: Cursor Replay Across Tenants

Mitigation: tenant identity is bound into cursor verification.

### Threat: Infinite Recursive Pagination

Mitigation: the initial Snapshot sequence is preserved across the pagination session.

### Threat: Split Audit Evidence

Mitigation: both APIs use the central tenant application router registry and one shared ledger path.

### Threat: Boundary Gate Failure

Mitigation: Fail-closed behavior, sanitized errors, and withholding of the original payload.

## Known Limitations

ARR-012 does not yet provide:

- Database encryption at rest
- Hardware-backed tenant key isolation
- Distributed ledger replication
- Production identity-provider integration
- Rate limiting
- Formal verification

These are production-hardening concerns outside the current application-boundary proof.

## Operational Requirements

1. Use the central tenant application router registry.
2. Configure one authoritative boundary-audit database path.
3. Prevent direct public access to canonical services and ledgers.
4. Preserve fail-closed boundary behavior.
5. Run the complete regression suite before release.
6. Review all new public fields against the boundary allowlist.
7. Add isolation tests for every new artifact type.
8. Preserve snapshot semantics for paginated audit reads.

## Definition of Done

- Tenant routers are registered in the real application.
- End-to-end two-tenant isolation tests pass.
- Public and canonical identities remain separated.
- Runtime response enforcement remains fail closed.
- Boundary decisions are immutably recorded.
- Tenant-scoped audit queries remain isolated and bounded.
- The full regression suite passes.
- Completion is pushed to Git.
