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
  const cancelButtonRef =
    useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    cancelButtonRef.current?.focus();

    function handleKeyDown(
      event: KeyboardEvent
    ) {
      if (
        event.key === "Escape" &&
        !busy
      ) {
        onCancel();
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown
    );

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown
      );

      document.body.style.overflow =
        previousOverflow;
    };
  }, [busy, onCancel, open]);

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
        role="dialog"
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
