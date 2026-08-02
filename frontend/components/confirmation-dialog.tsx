"use client";

import {
  useEffect,
  useRef
} from "react";

export type ConfirmationDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  busy?: boolean;
  tone?: "default" | "warning";
  onConfirm: () => void;
  onCancel: () => void;
};

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])"
].join(",");

export function ConfirmationDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Cancel",
  busy = false,
  tone = "default",
  onConfirm,
  onCancel
}: ConfirmationDialogProps) {
  const dialogRef =
    useRef<HTMLElement>(null);

  const cancelButtonRef =
    useRef<HTMLButtonElement>(null);

  const previouslyFocusedRef =
    useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    previouslyFocusedRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    window.requestAnimationFrame(() => {
      cancelButtonRef.current?.focus();
    });

    function handleKeyDown(
      event: KeyboardEvent
    ) {
      if (
        event.key === "Escape" &&
        !busy
      ) {
        event.preventDefault();
        onCancel();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const dialog =
        dialogRef.current;

      if (!dialog) {
        return;
      }

      const focusableElements =
        Array.from(
          dialog.querySelectorAll<HTMLElement>(
            FOCUSABLE_SELECTOR
          )
        ).filter(
          (element) =>
            !element.hasAttribute("disabled") &&
            element.getAttribute(
              "aria-hidden"
            ) !== "true"
        );

      if (
        focusableElements.length === 0
      ) {
        event.preventDefault();
        dialog.focus();
        return;
      }

      const first =
        focusableElements[0];

      const last =
        focusableElements[
          focusableElements.length - 1
        ];

      const active =
        document.activeElement;

      if (
        event.shiftKey &&
        active === first
      ) {
        event.preventDefault();
        last.focus();
        return;
      }

      if (
        !event.shiftKey &&
        active === last
      ) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown
      );

      document.body.style.overflow =
        previousOverflow;

      const previous =
        previouslyFocusedRef.current;

      window.requestAnimationFrame(() => {
        if (
          previous &&
          document.contains(previous)
        ) {
          previous.focus();
        }
      });
    };
  }, [
    busy,
    onCancel,
    open
  ]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target ===
            event.currentTarget &&
          !busy
        ) {
          onCancel();
        }
      }}
    >
      <section
        aria-describedby="confirmation-description"
        aria-labelledby="confirmation-title"
        aria-modal="true"
        className="confirmation-dialog"
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        <div
          className={
            tone === "warning"
              ? "dialog-icon dialog-icon-warning"
              : "dialog-icon"
          }
          aria-hidden="true"
        >
          !
        </div>

        <div>
          <p className="panel-kicker">
            Confirmation required
          </p>

          <h2 id="confirmation-title">
            {title}
          </h2>

          <p
            className="dialog-description"
            id="confirmation-description"
          >
            {description}
          </p>
        </div>

        <div className="dialog-actions">
          <button
            className="secondary-button"
            disabled={busy}
            onClick={onCancel}
            ref={cancelButtonRef}
            type="button"
          >
            {cancelLabel}
          </button>

          <button
            className={
              tone === "warning"
                ? "dialog-confirm-button dialog-confirm-warning"
                : "dialog-confirm-button"
            }
            disabled={busy}
            onClick={onConfirm}
            type="button"
          >
            {busy
              ? "Processing?"
              : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}
