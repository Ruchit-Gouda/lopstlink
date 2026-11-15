import { useEffect, useRef } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  busy = false,
  onCancel,
  onConfirm,
}) {
  const confirmRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    confirmRef.current?.focus();

    function handleKey(event) {
      if (event.key === "Escape" && !busy) onCancel();
    }

    window.addEventListener("keydown", handleKey);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKey);
    };
  }, [open, busy, onCancel]);

  if (!open) return null;

  return (
    <div
      className="modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onCancel();
      }}
    >
      <div
        className="modal__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <span className="modal__icon" aria-hidden="true">
          <AlertTriangle size={20} />
        </span>

        <h3 id="confirm-dialog-title">{title}</h3>
        <p>{description}</p>

        <div className="modal__actions">
          <button
            type="button"
            className="btn btn--ghost"
            onClick={onCancel}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            ref={confirmRef}
            type="button"
            className="btn btn--primary"
            onClick={onConfirm}
            disabled={busy}
          >
            {busy && <Loader2 size={16} className="spin" aria-hidden="true" />}
            {busy ? "Updating…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
