import {
  CalendarDays,
  CheckCircle2,
  ImageOff,
  Loader2,
  MapPin,
  Palette,
  Sparkles,
  Tag,
} from "lucide-react";
import { formatDate, reportTypeLabel } from "../utils/format";
import MatchList from "./MatchList";

export default function ReportCard({
  report,
  matchState,
  onFindMatches,
  onResolve,
  resolving,
}) {
  const isSearching = matchState?.status === "loading";

  return (
    <article className={`report-card report-card--${report.report_type}`}>
      <div className="report-card__media">
        {report.image_url ? (
          <a
            href={report.image_url}
            target="_blank"
            rel="noreferrer"
            aria-label={`Open photo of ${report.item_name}`}
          >
            <img
              src={report.image_url}
              alt={report.item_name}
              loading="lazy"
            />
          </a>
        ) : (
          <div className="report-card__placeholder">
            <ImageOff size={24} aria-hidden="true" />
            <span>No photo</span>
          </div>
        )}

        <span className={`badge badge--${report.report_type}`}>
          {reportTypeLabel(report.report_type)}
        </span>
      </div>

      <div className="report-card__body">
        <div className="report-card__title">
          <h3>{report.item_name}</h3>
          <span className="report-card__date">
            <CalendarDays size={13} aria-hidden="true" />
            {formatDate(report.event_date)}
          </span>
        </div>

        <p className="report-card__description">{report.description}</p>

        <div className="meta">
          <span className="meta__item">
            <Tag size={14} aria-hidden="true" />
            {report.category}
          </span>

          {report.color && (
            <span className="meta__item">
              <Palette size={14} aria-hidden="true" />
              {report.color}
            </span>
          )}

          {report.brand && (
            <span className="meta__item meta__item--plain">
              {report.brand}
            </span>
          )}

          <span className="meta__item">
            <MapPin size={14} aria-hidden="true" />
            {report.location_text}
          </span>
        </div>

        <div className="report-card__actions">
          <button
            type="button"
            className="btn btn--primary btn--sm"
            onClick={() => onFindMatches(report.id)}
            disabled={isSearching}
          >
            {isSearching ? (
              <Loader2 size={15} className="spin" aria-hidden="true" />
            ) : (
              <Sparkles size={15} aria-hidden="true" />
            )}
            {isSearching ? "Comparing…" : "Find matches"}
          </button>

          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={() => onResolve(report)}
            disabled={resolving}
          >
            {resolving ? (
              <Loader2 size={15} className="spin" aria-hidden="true" />
            ) : (
              <CheckCircle2 size={15} aria-hidden="true" />
            )}
            {resolving ? "Updating…" : "Mark resolved"}
          </button>
        </div>

        {matchState && (
          <MatchList
            state={matchState}
            onRetry={() => onFindMatches(report.id)}
          />
        )}
      </div>
    </article>
  );
}
