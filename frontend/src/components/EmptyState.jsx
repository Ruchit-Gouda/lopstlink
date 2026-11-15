import { Inbox, SearchX } from "lucide-react";

export default function EmptyState({ searching, onReset }) {
  const Icon = searching ? SearchX : Inbox;

  return (
    <div className="empty">
      <span className="empty__icon" aria-hidden="true">
        <Icon size={26} />
      </span>
      <h3>{searching ? "No reports match your search" : "No open reports yet"}</h3>
      <p>
        {searching
          ? "Try a different keyword or clear the filters."
          : "Be the first to report a lost or found item on campus."}
      </p>
      {searching && onReset && (
        <button type="button" className="btn btn--ghost btn--sm" onClick={onReset}>
          Clear filters
        </button>
      )}
    </div>
  );
}
