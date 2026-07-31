"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";

import {
  fetchDashboardSummary,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentDashboardSummary
} from "@/lib/governance-assessment-api";

type MetricCardProps = {
  label: string;
  value: string | number;
  detail: string;
};

function MetricCard({
  label,
  value,
  detail
}: MetricCardProps) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

function StatusBadge({
  healthy,
  healthyText,
  unhealthyText
}: {
  healthy: boolean;
  healthyText: string;
  unhealthyText: string;
}) {
  return (
    <span
      className={
        healthy
          ? "status-badge status-healthy"
          : "status-badge status-warning"
      }
    >
      <span className="status-dot" aria-hidden="true" />
      {healthy ? healthyText : unhealthyText}
    </span>
  );
}

export default function GovernanceAssessmentConsole() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [summary, setSummary] =
    useState<GovernanceAssessmentDashboardSummary | null>(
      null
    );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] =
    useState<string | null>(null);

  const loadSummary = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchDashboardSummary(
          config,
          signal
        );

        setSummary(result);
        setLastUpdated(
          new Date().toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit"
          })
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
            `Backend returned ${caught.status}. Verify the API is running and the console headers match the configured tenant.`
          );
        } else {
          setError(
            "The Governance Assessment backend could not be reached."
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

    void loadSummary(controller.signal);

    return () => controller.abort();
  }, [loadSummary]);

  const auditHealthy =
    summary?.audit_chain_valid ?? false;
  const signingEnabled =
    summary?.active_signing_key_id != null;

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="overview"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Governance Assessment
            </p>
            <h1>Operational Integrity Overview</h1>
            <p className="page-description">
              Monitor evidence, checkpoints, signing keys,
              and constitutional audit health.
            </p>
          </div>

          <div className="topbar-actions">
            {lastUpdated && (
              <p className="last-updated">
                Updated {lastUpdated}
              </p>
            )}
            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() => void loadSummary()}
            >
              {loading ? "Refreshing?" : "Refresh"}
            </button>
          </div>
        </header>

        {error && (
          <section className="error-panel" role="alert">
            <div>
              <p className="error-title">
                Dashboard unavailable
              </p>
              <p>{error}</p>
            </div>
            <button
              type="button"
              onClick={() => void loadSummary()}
            >
              Retry
            </button>
          </section>
        )}

        <section className="status-strip">
          <div>
            <p className="status-heading">
              Constitutional status
            </p>
            <StatusBadge
              healthy={auditHealthy}
              healthyText="Audit chain valid"
              unhealthyText="Audit review required"
            />
          </div>

          <div>
            <p className="status-heading">
              Signing posture
            </p>
            <StatusBadge
              healthy={signingEnabled}
              healthyText="Signing enabled"
              unhealthyText="Signing not configured"
            />
          </div>

          <div>
            <p className="status-heading">
              Active signing key
            </p>
            <p className="status-value">
              {summary?.active_signing_key_id ??
                "Not configured"}
            </p>
          </div>
        </section>

        <section
          className="metrics-grid"
          aria-label="Governance metrics"
        >
          <MetricCard
            label="Audit events"
            value={
              loading && !summary
                ? "?"
                : summary?.audit_event_count ?? 0
            }
            detail="Immutable governance activity"
          />
          <MetricCard
            label="Checkpoints"
            value={
              loading && !summary
                ? "?"
                : summary?.checkpoint_count ?? 0
            }
            detail="Recorded integrity checkpoints"
          />
          <MetricCard
            label="Signed checkpoints"
            value={
              loading && !summary
                ? "?"
                : summary?.signed_checkpoint_count ?? 0
            }
            detail="Cryptographically signed records"
          />
          <MetricCard
            label="Signing keys"
            value={
              loading && !summary
                ? "?"
                : summary?.signing_key_count ?? 0
            }
            detail="Active and historical keys"
          />
          <MetricCard
            label="Key activations"
            value={
              loading && !summary
                ? "?"
                : summary?.key_activation_event_count ?? 0
            }
            detail="Audited lifecycle operations"
          />
        </section>

        <section className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">
                  Evidence constitution
                </p>
                <h2>Integrity posture</h2>
              </div>
              <StatusBadge
                healthy={auditHealthy}
                healthyText="Healthy"
                unhealthyText="Review"
              />
            </div>

            <div className="integrity-visual">
              <div
                className={
                  auditHealthy
                    ? "integrity-ring integrity-ring-healthy"
                    : "integrity-ring"
                }
              >
                <span>
                  {auditHealthy ? "Valid" : "Review"}
                </span>
              </div>

              <div>
                <p className="integrity-title">
                  Audit chain verification
                </p>
                <p className="integrity-description">
                  The tenant evidence chain is evaluated by
                  the deterministic Governance Assessment
                  backend.
                </p>
              </div>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">
                  Deployment context
                </p>
                <h2>Console connection</h2>
              </div>
            </div>

            <dl className="connection-list">
              <div>
                <dt>API</dt>
                <dd>{config.baseUrl}</dd>
              </div>
              <div>
                <dt>Tenant</dt>
                <dd>{config.tenantId}</dd>
              </div>
              <div>
                <dt>Actor</dt>
                <dd>{config.actorId}</dd>
              </div>
              <div>
                <dt>Role</dt>
                <dd>{config.actorRoles}</dd>
              </div>
            </dl>
          </article>
        </section>
      </section>
    </main>
  );
}
