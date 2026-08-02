"use client";

import Link from "next/link";
import {
  useEffect,
  useRef,
  useState
} from "react";

type ConsoleSidebarPage =
  | "overview"
  | "assessments"
  | "evidence"
  | "audit-integrity"
  | "signing-keys"
  | "signed-checkpoints";

type ConsoleSidebarProps = {
  activePage: ConsoleSidebarPage;
  tenantId: string;
  actorId: string;
};

type NavigationItem = {
  href: string;
  label: string;
  page: ConsoleSidebarPage;
};

const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    href: "/",
    label: "Overview",
    page: "overview"
  },
  {
    href: "/assessments",
    label: "Assessments",
    page: "assessments"
  },
  {
    href: "/evidence",
    label: "Evidence",
    page: "evidence"
  },
  {
    href: "/audit-integrity",
    label: "Audit Integrity",
    page: "audit-integrity"
  },
  {
    href: "/signing-keys",
    label: "Signing Keys",
    page: "signing-keys"
  },
  {
    href: "/signed-checkpoints",
    label: "Signed Checkpoints",
    page: "signed-checkpoints"
  }
];

export function ConsoleSidebar({
  activePage,
  tenantId,
  actorId
}: ConsoleSidebarProps) {
  const [mobileOpen, setMobileOpen] =
    useState(false);

  const menuButtonRef =
    useRef<HTMLButtonElement>(null);

  const sidebarRef =
    useRef<HTMLElement>(null);

  function closeMobileNavigation(
    restoreFocus = false
  ) {
    setMobileOpen(false);

    if (restoreFocus) {
      window.requestAnimationFrame(() => {
        menuButtonRef.current?.focus();
      });
    }
  }

  useEffect(() => {
    if (!mobileOpen) {
      return;
    }

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    function handleKeyDown(
      event: KeyboardEvent
    ) {
      if (event.key === "Escape") {
        event.preventDefault();

        closeMobileNavigation(true);
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown
    );

    window.requestAnimationFrame(() => {
      const activeNavigationItem =
        sidebarRef.current?.querySelector<HTMLElement>(
          ".nav-item-active"
        );

      const firstNavigationItem =
        sidebarRef.current?.querySelector<HTMLElement>(
          ".nav-item"
        );

      (
        activeNavigationItem ??
        firstNavigationItem
      )?.focus();
    });

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown
      );

      document.body.style.overflow =
        previousOverflow;
    };
  }, [mobileOpen]);

  return (
    <>
      <button
        aria-controls="console-primary-sidebar"
        aria-expanded={mobileOpen}
        aria-label={
          mobileOpen
            ? "Close navigation menu"
            : "Open navigation menu"
        }
        className="mobile-navigation-button"
        onClick={() =>
          setMobileOpen((current) => !current)
        }
        ref={menuButtonRef}
        type="button"
      >
        <span
          aria-hidden="true"
          className="mobile-navigation-icon"
        >
          <span />
          <span />
          <span />
        </span>

        <span>Menu</span>
      </button>

      {mobileOpen && (
        <button
          aria-label="Close navigation menu"
          className="sidebar-backdrop"
          onClick={() =>
            closeMobileNavigation(true)
          }
          type="button"
        />
      )}

      <aside
        aria-label="Governance Console navigation"
        aria-modal={
          mobileOpen
            ? true
            : undefined
        }
        className={
          mobileOpen
            ? "sidebar sidebar-mobile-open"
            : "sidebar"
        }
        id="console-primary-sidebar"
        ref={sidebarRef}
        role={
          mobileOpen
            ? "dialog"
            : undefined
        }
      >
        <div className="sidebar-brand-row">
          <div className="sidebar-brand">
            <div
              aria-hidden="true"
              className="brand-mark"
            >
              G
            </div>

            <div className="brand-copy">
              <p className="brand-name">
                GAGF
              </p>

              <p className="brand-subtitle">
                Governance Console
              </p>
            </div>
          </div>

          <button
            aria-label="Close navigation menu"
            className="sidebar-close-button"
            onClick={() =>
              closeMobileNavigation(true)
            }
            type="button"
          >
            X
          </button>
        </div>

        <nav aria-label="Primary navigation">
          {NAVIGATION_ITEMS.map((item) => {
            const active =
              activePage === item.page;

            return (
              <Link
                aria-current={
                  active
                    ? "page"
                    : undefined
                }
                className={
                  active
                    ? "nav-item nav-item-active"
                    : "nav-item"
                }
                href={item.href}
                key={item.href}
                onClick={() =>
                  closeMobileNavigation(false)
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-label">
            Tenant
          </p>

          <p className="tenant-name">
            {tenantId}
          </p>

          <p className="actor-name">
            {actorId}
          </p>
        </div>
      </aside>
    </>
  );
}
