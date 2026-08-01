"use client";

import { useEffect } from "react";

export type ConsoleToastProps = {
  message: string | null;
  tone?: "success" | "error" | "info";
  durationMs?: number;
  onDismiss: () => void;
};

export function ConsoleToast({
  message,
  tone = "success",
  durationMs = 5000,
  onDismiss
}: ConsoleToastProps) {
  useEffect(() => {
    if (!message) {
      return;
    }

    const timeout = window.setTimeout(
      onDismiss,
      durationMs
    );

    return () => {
      window.clearTimeout(timeout);
    };
  }, [
    durationMs,
    message,
    onDismiss
  ]);

  if (!message) {
    return null;
  }

  return (
    <div
      aria-atomic="true"
      aria-live={
        tone === "error"
          ? "assertive"
          : "polite"
      }
      className={`console-toast console-toast-${tone}`}
      role={
        tone === "error"
          ? "alert"
          : "status"
      }
    >
      <span
        className="console-toast-indicator"
        aria-hidden="true"
      />

      <p>{message}</p>

      <button
        aria-label="Dismiss notification"
        onClick={onDismiss}
        type="button"
      >
        ?
      </button>
    </div>
  );
}
