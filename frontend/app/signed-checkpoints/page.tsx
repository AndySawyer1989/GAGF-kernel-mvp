"use client";


import { ConsoleSkipLink } from "@/components/console-skip-link";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConfirmationDialog } from "@/components/confirmation-dialog";
import { ConsolePagination } from "@/components/console-pagination";
import { ConsoleSidebar } from "@/components/console-sidebar";
import { ConsoleToast } from "@/components/console-toast";
import { SigningCapabilityPanel } from "@/components/signing-capability-panel";
import { SigningCapabilityAction } from "@/components/signing-capability-action";
import {
  createSignedAuditCheckpoint,
  fetchSignedAuditCheckpointRecords,
  fetchSignedAuditCheckpointVerificationRecords,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentCheckpointCreationResult,
  type GovernanceAssessmentSignedCheckpointList,
  type GovernanceAssessmentSignedCheckpointVerificationList
} from "@/lib/governance-assessment-api";
import {
  clampPageToItems,
  readPositiveIntegerParam,
  updateUrlParams
} from "@/lib/url-table-state";
import {
  detectSigningCapability,
  loadingSigningCapability,
  type SigningCapability
} from "@/lib/signing-capability";

const SIGNED_CHECKPOINT_PAGE_SIZE = 5;

function formatTimestamp(
  value: string
): string {
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

function shortHash(
  value: string,
  start = 12,
  end = 10
): string {
  if (value.length <= start + end + 1) {
    return value;
  }

  return `${value.slice(0, start)}?${value.slice(-end)}`;
}

export default function SignedCheckpointsPage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [records, setRecords] =
    useState<GovernanceAssessmentSignedCheckpointList | null>(
      null
    );

  const [verification, setVerification] =
    useState<GovernanceAssessmentSignedCheckpointVerificationList | null>(
      null
    );

  const [latestCreation, setLatestCreation] =
    useState<GovernanceAssessmentCheckpointCreationResult | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [
    signingCapability,
    setSigningCapability
  ] = useState<SigningCapability>(
    loadingSigningCapability
  );

  const [signedPage, setSignedPage] =
    useState(1);

  const [urlStateReady, setUrlStateReady] =
    useState(false);

  const [creating, setCreating] =
    useState(false);

  const [
    confirmCreateOpen,
    setConfirmCreateOpen
  ] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const loadSignedCheckpoints = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setSigningCapability(
        loadingSigningCapability()
      );

      try {
        const [
          signedRecords,
          verificationRecords,
          capability
        ] = await Promise.all([
          fetchSignedAuditCheckpointRecords(
            config,
            signal
          ),
          fetchSignedAuditCheckpointVerificationRecords(
            config,
            signal
          ),
          detectSigningCapability(
            config,
            signal
          )
        ]);

        setRecords(signedRecords);
        setVerification(verificationRecords);
        setSigningCapability(capability);
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
            `Backend returned ${caught.status} while loading signed checkpoints.`
          );
        } else {
          setError(
            "The Signed Checkpoint Console could not be loaded."
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
    setSignedPage(
      readPositiveIntegerParam(
        "signedPage"
      )
    );

    setUrlStateReady(true);
  }, []);

  useEffect(() => {
    if (!urlStateReady) {
      return;
    }

    updateUrlParams({
      signedPage
    });
  }, [
    signedPage,
    urlStateReady
  ]);

  useEffect(() => {
    const controller = new AbortController();

    void loadSignedCheckpoints(
      controller.signal
    );

    return () => controller.abort();
  }, [loadSignedCheckpoints]);

  async function createCheckpoint() {
    if (!signingCapability.available) {
      setConfirmCreateOpen(false);
      setError(
        signingCapability.message
      );
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);

    try {
      const created =
        await createSignedAuditCheckpoint(
          config
        );

      setLatestCreation(created);

      setNotice(
        created.signed
          ? `Checkpoint ${created.checkpoint.checkpoint_id} was created and signed.`
          : `Checkpoint ${created.checkpoint.checkpoint_id} was created without a signature.`
      );

      setConfirmCreateOpen(false);

      await loadSignedCheckpoints();
    } catch (caught) {
      if (
        caught instanceof GovernanceAssessmentApiError
      ) {
        setError(
          `Signed checkpoint creation failed with status ${caught.status}.`
        );
      } else {
        setError(
          "The signed checkpoint could not be created."
        );
      }
    } finally {
      setCreating(false);
    }
  }

  const signedItems =
    records?.items ?? [];

  const safeSignedPage =
    clampPageToItems(
      signedPage,
      signedItems.length,
      SIGNED_CHECKPOINT_PAGE_SIZE
    );

  const paginatedSignedItems =
    signedItems.slice(
      (safeSignedPage - 1) *
        SIGNED_CHECKPOINT_PAGE_SIZE,
      safeSignedPage *
        SIGNED_CHECKPOINT_PAGE_SIZE
    );

  const verificationByCheckpoint =
    useMemo(() => {
      return new Map(
        verification?.items.map((item) => [
          item.checkpoint_id,
          item
        ]) ?? []
      );
    }, [verification]);

  return (
    <main className="console-shell">
      <ConsoleSkipLink />
      <ConsoleSidebar
        activePage="signed-checkpoints"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace" id="console-main-content" tabIndex={-1}>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Cryptographic Audit Proof
            </p>

            <h1>Signed Checkpoints</h1>

            <p className="page-description">
              Create immutable audit checkpoints,
              sign them with the active durable key,
              and verify persisted signature proof.
            </p>
          </div>

          <div className="topbar-actions">
            <Link
              className="secondary-button"
              href="/audit-integrity"
            >
              Audit integrity
            </Link>

            <Link
              className="secondary-button"
              href="/signing-keys"
            >
              Signing keys
            </Link>

            <SigningCapabilityAction
              busy={creating}
              capability={signingCapability}
              loading={loading}
              onActivate={() =>
                setConfirmCreateOpen(true)
              }
            />
          </div>
        </header>

        <div id="signed-checkpoint-capability-help">
          <SigningCapabilityPanel
            capability={signingCapability}
            compact
          />
        </div>

        {error && (
          <section
            className="error-panel"
            role="alert"
          >
            <div>
              <p className="error-title">
                Signed checkpoint operation failed
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() =>
                void loadSignedCheckpoints()
              }
            >
              Retry
            </button>
          </section>
        )}

        <ConsoleToast
          message={notice}
          onDismiss={() =>
            setNotice(null)
          }
          tone="success"
        />

        {!error && loading && (
          <section className="detail-loading">
            <div className="loading-pulse" />
            <div className="loading-pulse" />
            <div className="loading-pulse" />
          </section>
        )}

        {!error &&
          !loading &&
          records &&
          verification && (
            <>
              <section className="signed-status-strip">
                <div>
                  <p className="status-heading">
                    Signing workflow
                  </p>

                  <span className="status-badge status-healthy">
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />
                    Operational
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Signed records
                  </p>
                  <p className="status-value">
                    {records.count}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Valid signatures
                  </p>
                  <p className="status-value">
                    {verification.valid_count}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Invalid signatures
                  </p>
                  <p className="status-value">
                    {verification.invalid_count}
                  </p>
                </div>
              </section>

              {latestCreation && (
                <section className="panel latest-signature-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Latest operation
                      </p>
                      <h2>
                        Signed checkpoint created
                      </h2>
                    </div>

                    <span
                      className={
                        latestCreation.signed
                          ? "status-badge status-healthy"
                          : "status-badge status-warning"
                      }
                    >
                      {latestCreation.signed
                        ? "Signed"
                        : "Unsigned"}
                    </span>
                  </div>

                  <dl className="connection-list">
                    <div>
                      <dt>Checkpoint ID</dt>
                      <dd>
                        {
                          latestCreation.checkpoint
                            .checkpoint_id
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Signing key</dt>
                      <dd>
                        {latestCreation.key_id}
                      </dd>
                    </div>

                    <div>
                      <dt>Algorithm</dt>
                      <dd>
                        {
                          latestCreation
                            .signature_algorithm
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Signature version</dt>
                      <dd>
                        {
                          latestCreation
                            .signature_version
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Signature</dt>
                      <dd>
                        <code
                          title={
                            latestCreation.signature
                          }
                        >
                          {shortHash(
                            latestCreation.signature
                          )}
                        </code>
                      </dd>
                    </div>
                  </dl>
                </section>
              )}

              <section className="result-metrics-grid">
                <article className="result-metric">
                  <p>Verification coverage</p>
                  <strong>
                    {records.count === 0
                      ? "0%"
                      : `${Math.round(
                          (
                            verification.count /
                            records.count
                          ) * 100
                        )}%`}
                  </strong>
                  <span>
                    Signed records checked
                  </span>
                </article>

                <article className="result-metric">
                  <p>Valid rate</p>
                  <strong>
                    {verification.count === 0
                      ? "0%"
                      : `${Math.round(
                          (
                            verification.valid_count /
                            verification.count
                          ) * 100
                        )}%`}
                  </strong>
                  <span>
                    Successful cryptographic proof
                  </span>
                </article>

                <article className="result-metric">
                  <p>Tenant</p>
                  <strong className="metric-date">
                    {records.tenant_id}
                  </strong>
                  <span>
                    Isolated signing boundary
                  </span>
                </article>

                <article className="result-metric">
                  <p>Result limit</p>
                  <strong>
                    {records.limit}
                  </strong>
                  <span>
                    Maximum records in view
                  </span>
                </article>
              </section>

              <section className="panel signed-inventory-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Persisted cryptographic evidence
                    </p>
                    <h2>
                      Signed checkpoint inventory
                    </h2>
                  </div>

                  <span className="status-value">
                    {records.count} signed
                  </span>
                </div>

                {records.items.length === 0 ? (
                  <div className="audit-empty">
                    No signed checkpoints exist for
                    this tenant.
                  </div>
                ) : (
                  <div className="signed-checkpoint-list">
                    {paginatedSignedItems.map((record) => {
                      const result =
                        verificationByCheckpoint.get(
                          record.checkpoint
                            .checkpoint_id
                        );

                      return (
                        <article
                          className="signed-checkpoint-card"
                          key={
                            record.checkpoint
                              .checkpoint_id
                          }
                        >
                          <div className="signed-card-heading">
                            <div>
                              <p className="panel-kicker">
                                Checkpoint
                              </p>

                              <h3>
                                {
                                  record.checkpoint
                                    .checkpoint_id
                                }
                              </h3>
                            </div>

                            <span
                              className={
                                result?.valid
                                  ? "status-badge status-healthy"
                                  : "status-badge status-warning"
                              }
                            >
                              {result?.valid
                                ? "Signature valid"
                                : "Verification failed"}
                            </span>
                          </div>

                          <div className="signed-proof-grid">
                            <div>
                              <span>Created</span>
                              <strong>
                                {formatTimestamp(
                                  record.checkpoint
                                    .created_at
                                )}
                              </strong>
                            </div>

                            <div>
                              <span>Events checked</span>
                              <strong>
                                {
                                  record.checkpoint
                                    .checked_count
                                }
                              </strong>
                            </div>

                            <div>
                              <span>Signing key</span>
                              <strong>
                                {record.key_id}
                              </strong>
                            </div>

                            <div>
                              <span>Algorithm</span>
                              <strong>
                                {
                                  record
                                    .signature_algorithm
                                }
                              </strong>
                            </div>

                            <div>
                              <span>
                                Checkpoint version
                              </span>
                              <strong>
                                {
                                  record.checkpoint
                                    .checkpoint_version
                                }
                              </strong>
                            </div>

                            <div>
                              <span>
                                Signature version
                              </span>
                              <strong>
                                {
                                  record
                                    .signature_version
                                }
                              </strong>
                            </div>
                          </div>

                          <div className="signed-hash-lineage">
                            <div>
                              <span>Chain head</span>
                              <code
                                title={
                                  record.checkpoint
                                    .chain_head_hash
                                }
                              >
                                {shortHash(
                                  record.checkpoint
                                    .chain_head_hash
                                )}
                              </code>
                            </div>

                            <div>
                              <span>Signature</span>
                              <code
                                title={
                                  record.signature
                                }
                              >
                                {shortHash(
                                  record.signature
                                )}
                              </code>
                            </div>
                          </div>

                          {result?.reason_code && (
                            <div className="signed-reason">
                              <strong>
                                Verification reason
                              </strong>
                              <code>
                                {result.reason_code}
                              </code>
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}

                <ConsolePagination
                  currentPage={safeSignedPage}
                  label="Signed checkpoints"
                  onPageChange={setSignedPage}
                  pageSize={
                    SIGNED_CHECKPOINT_PAGE_SIZE
                  }
                  totalItems={signedItems.length}
                />
              </section>
            </>
          )}
      </section>

      <ConfirmationDialog
        busy={creating}
        confirmLabel="Create and sign"
        description={
          "This creates a new immutable tenant audit checkpoint, signs it with the active durable key, and persists the resulting cryptographic proof."
        }
        onCancel={() =>
          setConfirmCreateOpen(false)
        }
        onConfirm={() =>
          void createCheckpoint()
        }
        open={
          confirmCreateOpen &&
          signingCapability.available
        }
        title="Create a signed checkpoint?"
      />
    </main>
  );
}
