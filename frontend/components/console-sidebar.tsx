import Link from "next/link";

type ConsoleSidebarProps = {
  activePage:
    | "overview"
    | "assessments"
    | "evidence"
    | "audit-integrity"
    | "signing-keys";
  tenantId: string;
  actorId: string;
};

export function ConsoleSidebar({
  activePage,
  tenantId,
  actorId
}: ConsoleSidebarProps) {
  return (
    <aside className="sidebar">
      <div>
        <div className="brand-mark">G</div>
        <div className="brand-copy">
          <p className="brand-name">GAGF</p>
          <p className="brand-subtitle">
            Governance Console
          </p>
        </div>
      </div>

      <nav aria-label="Primary navigation">
        <Link
          className={
            activePage === "overview"
              ? "nav-item nav-item-active"
              : "nav-item"
          }
          href="/"
        >
          Overview
        </Link>

        <Link
          className={
            activePage === "assessments"
              ? "nav-item nav-item-active"
              : "nav-item"
          }
          href="/assessments"
        >
          Assessments
        </Link>

        <Link
          className={
            activePage === "evidence"
              ? "nav-item nav-item-active"
              : "nav-item"
          }
          href="/evidence"
        >
          Evidence
        </Link>

        <Link
          className={
            activePage === "audit-integrity"
              ? "nav-item nav-item-active"
              : "nav-item"
          }
          href="/audit-integrity"
        >
          Audit Integrity
        </Link>

        <Link
          className={
            activePage === "signing-keys"
              ? "nav-item nav-item-active"
              : "nav-item"
          }
          href="/signing-keys"
        >
          Signing Keys
        </Link>
      </nav>

      <div className="sidebar-footer">
        <p className="sidebar-label">Tenant</p>
        <p className="tenant-name">{tenantId}</p>
        <p className="actor-name">{actorId}</p>
      </div>
    </aside>
  );
}
