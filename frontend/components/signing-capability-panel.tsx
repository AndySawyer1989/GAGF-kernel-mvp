import type {
  SigningCapability
} from "@/lib/signing-capability";

type SigningCapabilityPanelProps = {
  capability: SigningCapability;
  compact?: boolean;
};

function statusLabel(
  capability: SigningCapability
): string {
  switch (capability.status) {
    case "loading":
      return "Checking";
    case "available":
      return "Available";
    case "unconfigured":
      return "Not configured";
    case "unauthorized":
      return "Access denied";
    case "unreachable":
      return "Unreachable";
    case "error":
      return "Unknown";
  }
}

function statusClass(
  capability: SigningCapability
): string {
  switch (capability.status) {
    case "available":
      return "status-badge status-healthy";

    case "loading":
      return "status-badge status-neutral";

    case "unconfigured":
    case "unauthorized":
    case "unreachable":
    case "error":
      return "status-badge status-warning";
  }
}

export function SigningCapabilityPanel({
  capability,
  compact = false
}: SigningCapabilityPanelProps) {
  return (
    <section
      aria-live="polite"
      className={
        compact
          ? "signing-capability-panel signing-capability-compact"
          : "signing-capability-panel"
      }
      data-capability-status={capability.status}
    >
      <div className="signing-capability-heading">
        <div>
          <p className="panel-kicker">
            Runtime capability
          </p>

          <h2>{capability.title}</h2>
        </div>

        <span
          className={statusClass(capability)}
        >
          <span
            aria-hidden="true"
            className="status-dot"
          />

          {statusLabel(capability)}
        </span>
      </div>

      <p>{capability.message}</p>

      {capability.activeKey && (
        <dl className="signing-capability-details">
          <div>
            <dt>Active key</dt>
            <dd>
              <code>
                {capability.activeKey.key_id}
              </code>
            </dd>
          </div>

          <div>
            <dt>Tenant</dt>
            <dd>
              {capability.activeKey.tenant_id}
            </dd>
          </div>
        </dl>
      )}

      {!capability.available &&
        capability.status !== "loading" && (
          <p className="signing-capability-continuity">
            Existing signed checkpoints and
            verification evidence remain available
            in read-only mode.
          </p>
        )}
    </section>
  );
}
