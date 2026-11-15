export default function SkeletonCard() {
  return (
    <div className="report-card report-card--skeleton" aria-hidden="true">
      <div className="skeleton skeleton--media" />
      <div className="report-card__body">
        <div className="skeleton skeleton--title" />
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--line skeleton--short" />
        <div className="skeleton skeleton--chip" />
      </div>
    </div>
  );
}
