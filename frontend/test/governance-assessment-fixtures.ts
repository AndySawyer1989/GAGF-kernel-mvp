export const TEST_TENANT_ID =
  "tenant-alpha";

export const TEST_ACTOR_ID =
  "console-admin";

export const TEST_ACTOR_ROLES =
  "assessment:admin";

export const TEST_SIGNING_KEY_ID =
  "assessment-local-2026-01";

export function createTestApiConfig(
  overrides: Record<string, unknown> = {}
) {
  return {
    baseUrl:
      "http://127.0.0.1:8000",
    tenantId: TEST_TENANT_ID,
    actorId: TEST_ACTOR_ID,
    actorRoles: TEST_ACTOR_ROLES,
    ...overrides
  };
}

export function createActiveSigningKey(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: TEST_TENANT_ID,
    key_id: TEST_SIGNING_KEY_ID,
    secret_reference:
      "env://GAGF_ASSESSMENT_CHECKPOINT_SECRET",
    active: true,
    created_at:
      "2026-08-02T12:00:00Z",
    retired_at: null,
    ...overrides
  };
}

export function createAuditCheckpoint(
  overrides: Record<string, unknown> = {}
) {
  return {
    checkpoint_id:
      "checkpoint-test-001",
    tenant_id: TEST_TENANT_ID,
    chain_head_hash:
      "chain-head-hash-test-001",
    checked_count: 461,
    valid: true,
    reason_code: null,
    created_at:
      "2026-08-03T00:01:00Z",
    checkpoint_version: "1.0.0",
    ...overrides
  };
}

export function createSignedCheckpointRecord(
  overrides: Record<string, unknown> = {}
) {
  return {
    checkpoint: createAuditCheckpoint(),
    key_id: TEST_SIGNING_KEY_ID,
    signature:
      "signature-value-test-001",
    signature_algorithm:
      "hmac-sha256",
    signature_version: "1.0.0",
    ...overrides
  };
}

export function createSignedCheckpointList(
  overrides: Record<string, unknown> = {}
) {
  const item =
    createSignedCheckpointRecord();

  return {
    tenant_id: TEST_TENANT_ID,
    items: [item],
    count: 1,
    limit: 100,
    ...overrides
  };
}

export function createSignedVerificationItem(
  overrides: Record<string, unknown> = {}
) {
  return {
    checkpoint_id:
      "checkpoint-test-001",
    key_id: TEST_SIGNING_KEY_ID,
    valid: true,
    reason_code: null,
    ...overrides
  };
}

export function createSignedVerificationList(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: TEST_TENANT_ID,
    items: [
      createSignedVerificationItem()
    ],
    count: 1,
    valid_count: 1,
    invalid_count: 0,
    limit: 100,
    ...overrides
  };
}

export function createAuditEvent(
  overrides: Record<string, unknown> = {}
) {
  return {
    event_id:
      "audit-event-test-001",
    request_id:
      "request-test-001",
    tenant_id: TEST_TENANT_ID,
    actor_id:
      "integration-operator",
    actor_roles: [
      TEST_ACTOR_ROLES
    ],
    method: "POST",
    route:
      "/api/v1/governance-assessments/execute",
    outcome: "allowed",
    status_code: 200,
    reason_code: null,
    occurred_at:
      "2026-08-03T00:00:00Z",
    previous_hash:
      "previous-audit-hash-test",
    event_hash:
      "current-audit-hash-test",
    hash_version: "1.0.0",
    ...overrides
  };
}

export function createAuditEventList(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: TEST_TENANT_ID,
    items: [
      createAuditEvent()
    ],
    count: 1,
    limit: 100,
    ...overrides
  };
}

export function createAuditIntegrity(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: TEST_TENANT_ID,
    valid: true,
    checked_count: 461,
    failure_index: null,
    failure_event_id: null,
    reason_code: null,
    ...overrides
  };
}

export function createAuditCheckpointList(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: TEST_TENANT_ID,
    items: [
      createAuditCheckpoint()
    ],
    count: 1,
    limit: 100,
    ...overrides
  };
}

export function createAvailableSigningCapability(
  overrides: Record<string, unknown> = {}
) {
  return {
    status: "available" as const,
    available: true,
    title:
      "Durable signing available",
    message:
      `Checkpoint signing is available through active key ${TEST_SIGNING_KEY_ID}.`,
    activeKey:
      createActiveSigningKey(),
    statusCode: 200,
    reasonCode: null,
    ...overrides
  };
}

export function createUnconfiguredSigningCapability(
  overrides: Record<string, unknown> = {}
) {
  return {
    status: "unconfigured" as const,
    available: false,
    title:
      "Durable signing is not configured",
    message:
      "No active durable signing key is available for this tenant.",
    activeKey: null,
    statusCode: 503,
    reasonCode:
      "CHECKPOINT_SIGNING_UNAVAILABLE",
    ...overrides
  };
}

export function createUnauthorizedSigningCapability(
  overrides: Record<string, unknown> = {}
) {
  return {
    status: "unauthorized" as const,
    available: false,
    title:
      "Signing access is unauthorized",
    message:
      "Your current identity is not authorized to use durable checkpoint signing.",
    activeKey: null,
    statusCode: 403,
    reasonCode:
      "CHECKPOINT_SIGNING_FORBIDDEN",
    ...overrides
  };
}

export function createUnreachableSigningCapability(
  overrides: Record<string, unknown> = {}
) {
  return {
    status: "unreachable" as const,
    available: false,
    title:
      "Signing service is unreachable",
    message:
      "The Console could not reach the durable signing service.",
    activeKey: null,
    statusCode: null,
    reasonCode:
      "SIGNING_SERVICE_UNREACHABLE",
    ...overrides
  };
}
