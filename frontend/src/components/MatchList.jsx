import { AlertCircle, ImageOff, Loader2, MapPin, RefreshCw } from "lucide-react";
import {
  formatDate,
  reportTypeLabel,
  scoreLabel,
  scoreTone,
} from "../utils/format";

export default function MatchList({ state, onRetry }) {
  if (state.status === "loading") {
    return (
      <div className="matches">
        <div className="matches__status">
          <Loader2 size={17} className="spin" aria-hidden="true" />
          Comparing with other reports…
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="matches matches--error">
        <div className="matches__status">
          <AlertCircle size={17} aria-hidden="true" />
          {state.error}
        </div>
        <button type="button" className="btn btn--ghost btn--sm" onClick={onRetry}>
          <RefreshCw size={14} aria-hidden="true" />
          Try again
        </button>
      </div>
    );
  }

  const matches = state.data || [];

  return (
    <div className="matches">
      <div className="matches__header">
        <h4>Possible matches</h4>
        <span className="count-pill count-pill--sm">{matches.length}</span>
      </div>

      {matches.length === 0 ? (
        <p className="matches__empty">
          No strong matches yet. Check back as more reports come in.
        </p>
      ) : (
        <ul className="match-list">
          {matches.map(({ report, similarity_score, match_reasons }) => {
            const tone = scoreTone(similarity_score);

            return (
              <li className="match" key={report.id}>
                <div className="match__thumb">
                  {report.image_url ? (
                    <img
                      src={report.image_url}
                      alt={report.item_name}
                      loading="lazy"
                    />
                  ) : (
                    <ImageOff size={18} aria-hidden="true" />
                  )}
                </div>

                <div className="match__body">
                  <div className="match__title">
                    <strong>{report.item_name}</strong>
                    <span className={`badge badge--${report.report_type} badge--sm`}>
                      {reportTypeLabel(report.report_type)}
                    </span>
                  </div>

                  <p className="match__meta">
                    <MapPin size={12} aria-hidden="true" />
                    {report.location_text}
                    <span aria-hidden="true">·</span>
                    {formatDate(report.event_date)}
                  </p>

                  {match_reasons?.length > 0 && (
                    <div className="match__reasons">
                      {match_reasons.map((reason) => (
                        <span key={reason}>{reason}</span>
                      ))}
                    </div>
                  )}
                </div>

                <div className={`score score--${tone}`}>
                  <strong>{Math.round(similarity_score)}%</strong>
                  <span>{scoreLabel(similarity_score)}</span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
