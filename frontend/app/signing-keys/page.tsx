"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  activateSigningKey,
  fetchActiveSigningKey,
  fetchSignedCheckpointVerification,
  fetchSigningKeyAuditEvents,
  fetchSigningKeys,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentSignedCheckpointVerification,
  type GovernanceAssessmentSigningKey,
  type GovernanceAssessmentSigningKeyAuditList,
  type GovernanceAssessmentSigningKeyList
} from "@/lib/governance-assessment-api";

function formatTimestamp(
  value: string | null | undefined
): string {
  if (!value) {
    return "Not recorded";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  });
}

function maskSecretReference(
  value: string
): string {
  if (!value.startsWith("env://")) {
    return "External secret reference";
  }

  return value;
}

function renderAuditEvent(
  event: Record<string, unknown>,
  index: number
) {
  const eventType =
    typeof event.event_type === "string"
      ? event.event_type
      : "Signing key event";

  const actorId =
    typeof event.actor_id === "string"
      ? event.actor_id
      : "Unknown actor";

  const occurredAt =
    typeof event.occurred_at === "string"
      ? event.occurred_at
      : typeof event.created_at === "string"
        ? event.created_at
        : undefined;

  const activeKeyId =
    typeof event.active_key_id === "string"
      ? event.active_key_id
      : "Not recorded";

  const previousKeyId =
    typeof event.previous_key_id === "string"
      ? event.previous_key_id
      : "None";

  return (
    <article
      className="key-audit-event"
      key={
        typeof event.event_id === "string"
          ? event.event_id
          : `${eventType}-${index}`
      }
    >
      <div>
        <p className="panel-kicker">
          {eventType}
        </p>
        <strong>{activeKeyId}</strong>
        <span>
          Previous key: {previousKeyId}
        </span>
      </div>

      <div className="key-audit-meta">
        <span>{actorId}</span>
        <span>{formatTimestamp(occurredAt)}</span>
      </div>
    </article>
  );
}

export default function SigningKeysPage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [keys, setKeys] =
    useState<GovernanceAssessmentSigningKeyList | null>(
      null
    );

  const [activeKey, setActiveKey] =
    useState<GovernanceAssessmentSigningKey | null>(
      null
    );

  const [auditEvents, setAuditEvents] =
    useState<GovernanceAssessmentSigningKeyAuditList | null>(
      null
    );

  const [verification, setVerification] =
    useState<GovernanceAssessmentSignedCheckpointVerification | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [activatingKeyId, setActivatingKeyId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const loadSigningKeys = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const [
          keyList,
          active,
          audit,
          signedVerification
        ] = await Promise.all([
          fetchSigningKeys(config, signal),
          fetchActiveSigningKey(config, signal),
          fetchSigningKeyAuditEvents(
            config,
            signal
          ),
          fetchSignedCheckpointVerification(
            config,
            signal
          )
        ]);

        setKeys(keyList);
        setActiveKey(active);
        setAuditEvents(audit);
        setVerification(
          signedVerification
        );
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return;
        }

        if (
          caught instanceof GovernanceAssessmentApiError
        ) {
          setError(
            `Backend returned ${caught.status} while loading signing-key administration.`
          );
        } else {
          setError(
            "The Signing Key Console could not be loaded."
          );
        }
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [config]
  );

  useEffect(() => {
    const controller = new AbortController();

    void loadSigningKeys(controller.signal);

    return () => controller.abort();
  }, [loadSigningKeys]);

  async function activateKey(
    keyId: string
  ) {
    setActivatingKeyId(keyId);
    setError(null);
    setNotice(null);

    try {
      await activateSigningKey(
        config,
        keyId
      );

      setNotice(
        `Signing key ${keyId} is now active.`
      );

      await loadSigningKeys();
    } catch (caught) {
      if (
        caught instanceof GovernanceAssessmentApiError
      ) {
        setError(
          `Signing key activation failed with status ${caught.status}.`
        );
      } else {
        setError(
          "The signing key could not be activated."
        );
      }
    } finally {
      setActivatingKeyId(null);
    }
  }

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="signing-keys"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Cryptographic Administration
            </p>
            <h1>Signing Keys</h1>
            <p className="page-description">
              Inspect durable checkpoint signing
              metadata, active-key posture, signed
              checkpoint verification, and key
              activation evidence.
            </p>
          </div>

          <button
            className="refresh-button"
            type="button"
            disabled={loading}
            onClick={() =>
              void loadSigningKeys()
            }
          >
            {loading ? "Refreshing?" : "Refresh"}
          </button>
        </header>

        {error && (
          <section
            className="error-panel"
            role="alert"
          >
            <div>
              <p className="error-title">
                Signing-key console unavailable
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() =>
                void loadSigningKeys()
              }
            >
              Retry
            </button>
          </section>
        )}

        {notice && (
          <section
            className="audit-notice"
            aria-live="polite"
          >
            {notice}
          </section>
        )}

        {!error && loading && (
          <section className="detail-loading">
            <div className="loading-pulse" />
            <div className="loading-pulse" />
            <div className="loading-pulse" />
          </section>
        )}

        {!error &&
          !loading &&
          keys &&
          activeKey &&
          auditEvents &&
          verification && (
            <>
              <section className="signing-status-strip">
                <div>
                  <p className="status-heading">
                    Signing service
                  </p>
                  <span className="status-badge status-healthy">
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />
                    Available
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Active key
                  </p>
                  <p className="status-value signing-key-id">
                    {activeKey.key_id}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Registered keys
                  </p>
                  <p className="status-value">
                    {keys.count}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Signed checkpoints
                  </p>
                  <p className="status-value">
                    {verification.count}
                  </p>
                </div>
              </section>

              <section className="result-metrics-grid">
                <article className="result-metric">
                  <p>Valid signatures</p>
                  <strong>
                    {verification.valid_count}
                  </strong>
                  <span>
                    Cryptographically verified
                  </span>
                </article>

                <article className="result-metric">
                  <p>Invalid signatures</p>
                  <strong>
                    {verification.invalid_count}
                  </strong>
                  <span>
                    Failed verification
                  </span>
                </article>

                <article className="result-metric">
                  <p>Rotation events</p>
                  <strong>
                    {auditEvents.count}
                  </strong>
                  <span>
                    Key activation evidence
                  </span>
                </article>

                <article className="result-metric">
                  <p>Active since</p>
                  <strong className="metric-date">
                    {formatTimestamp(
                      activeKey.created_at
                    )}
                  </strong>
                  <span>
                    Current metadata record
                  </span>
                </article>
              </section>

              <section className="signing-grid">
                <article className="panel active-key-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Current authority
                      </p>
                      <h2>Active signing key</h2>
                    </div>

                    <span className="status-badge status-healthy">
                      Active
                    </span>
                  </div>

                  <dl className="connection-list">
                    <div>
                      <dt>Tenant</dt>
                      <dd>{activeKey.tenant_id}</dd>
                    </div>

                    <div>
                      <dt>Key ID</dt>
                      <dd>{activeKey.key_id}</dd>
                    </div>

                    <div>
                      <dt>Secret source</dt>
                      <dd>
                        <code>
                          {maskSecretReference(
                            activeKey.secret_reference
                          )}
                        </code>
                      </dd>
                    </div>

                    <div>
                      <dt>Created</dt>
                      <dd>
                        {formatTimestamp(
                          activeKey.created_at
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Retired</dt>
                      <dd>
                        {formatTimestamp(
                          activeKey.retired_at
                        )}
                      </dd>
                    </div>
                  </dl>

                  <div className="secret-safety-note">
                    <strong>
                      Secret-safe metadata
                    </strong>
                    <p>
                      The Console displays only the
                      external secret reference. The
                      signing secret itself is never
                      returned by the API.
                    </p>
                  </div>
                </article>

                <article className="panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Verification posture
                      </p>
                      <h2>
                        Signed checkpoint readiness
                      </h2>
                    </div>

                    <span className="status-badge status-healthy">
                      Ready
                    </span>
                  </div>

                  <dl className="connection-list">
                    <div>
                      <dt>Total checked</dt>
                      <dd>{verification.count}</dd>
                    </div>

                    <div>
                      <dt>Valid</dt>
                      <dd>
                        {verification.valid_count}
                      </dd>
                    </div>

                    <div>
                      <dt>Invalid</dt>
                      <dd>
                        {verification.invalid_count}
                      </dd>
                    </div>

                    <div>
                      <dt>Result limit</dt>
                      <dd>{verification.limit}</dd>
                    </div>
                  </dl>

                  {verification.count === 0 && (
                    <div className="audit-empty">
                      The signing service is ready,
                      but no signed audit checkpoints
                      exist yet.
                    </div>
                  )}
                </article>
              </section>

              <section className="panel key-registry-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Durable metadata registry
                    </p>
                    <h2>Registered signing keys</h2>
                  </div>

                  <span className="status-value">
                    {keys.count} key
                    {keys.count === 1 ? "" : "s"}
                  </span>
                </div>

                <div className="key-registry-table">
                  <div className="key-registry-header">
                    <span>Key ID</span>
                    <span>Secret reference</span>
                    <span>Created</span>
                    <span>Status</span>
                    <span>Action</span>
                  </div>

                  {keys.items.map((key) => (
                    <div
                      className="key-registry-row"
                      key={key.key_id}
                    >
                      <strong>{key.key_id}</strong>

                      <code title={key.secret_reference}>
                        {maskSecretReference(
                          key.secret_reference
                        )}
                      </code>

                      <span>
                        {formatTimestamp(
                          key.created_at
                        )}
                      </span>

                      <span
                        className={
                          key.active
                            ? "status-badge status-healthy"
                            : "status-badge status-neutral"
                        }
                      >
                        {key.active
                          ? "Active"
                          : "Inactive"}
                      </span>

                      <button
                        className="compact-action-button"
                        type="button"
                        disabled={
                          key.active ||
                          activatingKeyId !== null
                        }
                        onClick={() =>
                          void activateKey(
                            key.key_id
                          )
                        }
                      >
                        {activatingKeyId === key.key_id
                          ? "Activating?"
                          : key.active
                            ? "Current key"
                            : "Activate"}
                      </button>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel key-audit-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Administrative evidence
                    </p>
                    <h2>
                      Key activation history
                    </h2>
                  </div>

                  <span className="status-value">
                    {auditEvents.count}
                  </span>
                </div>

                {auditEvents.items.length === 0 ? (
                  <div className="audit-empty">
                    No administrative key activation
                    events have been recorded yet.
                    Bootstrap registration does not
                    create an activation event.
                  </div>
                ) : (
                  <div className="key-audit-list">
                    {auditEvents.items.map(
                      (event, index) =>
                        renderAuditEvent(
                          event,
                          index
                        )
                    )}
                  </div>
                )}
              </section>
            </>
          )}
      </section>
    </main>
  );
}
