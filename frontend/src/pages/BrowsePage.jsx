import {
  AlertCircle,
  ChevronRight,
  Home,
  PackageOpen,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import AppLink from "../components/AppLink";
import EmptyState from "../components/EmptyState";
import FilterBar from "../components/FilterBar";
import ReportCard from "../components/ReportCard";
import ReportForm from "../components/ReportForm";
import SkeletonCard from "../components/SkeletonCard";
import { routeForFilter } from "../router";
import { filterReports } from "../utils/reports";

const COPY = {
  all: {
    eyebrow: "Community feed",
    title: "All open reports",
    description:
      "Everything the community has reported, in one place. Search by item, colour or location, or publish something new.",
    feedTitle: "Open reports",
    feedHint: "Browse reports or search for a possible match.",
    icon: Sparkles,
  },
  lost: {
    eyebrow: "Lost category",
    title: "Lost reports",
    description:
      "Items the community is hoping to get back. Open a report to see how the match engine compares it with found items.",
    feedTitle: "Lost items",
    feedHint: "Every lost report, newest first.",
    icon: Search,
  },
  found: {
    eyebrow: "Found category",
    title: "Found reports",
    description:
      "Items waiting to be claimed. If something looks familiar, open the report and check the possible matches.",
    feedTitle: "Found items",
    feedHint: "Every found report, newest first.",
    icon: PackageOpen,
  },
};

const FILTER_LABELS = {
  all: "reports",
  lost: "lost reports",
  found: "found reports",
};

export default function BrowsePage({
  route,
  counts,
  reports,
  loading,
  loadError,
  onRefresh,
  user,
  onRequireAuth,
  onCreated,
  matchesByReport,
  onFindMatches,
  query,
  onQueryChange,
  onNavigate,
  initialType,
  formKey,
}) {
  const filter = route.filter;
  const copy = COPY[filter] || COPY.all;
  const Icon = copy.icon;
  const normalizedQuery = query.trim();
  const visibleReports = filterReports(reports, filter, query);
  const hasFilters = filter !== "all" || normalizedQuery.length > 0;

  function resetFilters() {
    onQueryChange("");
    onNavigate("/browse");
  }

  function scrollToForm() {
    document
      .getElementById("report-form")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="browse">
      <div className="browse-head">
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <AppLink to="/" onNavigate={onNavigate}>
            <Home size={13} aria-hidden="true" />
            Home
          </AppLink>
          <ChevronRight size={13} aria-hidden="true" />
          <span>{copy.title}</span>
        </nav>

        <div className="browse-head__row">
          <div className="browse-head__copy">
            <span className="eyebrow">
              <Icon size={14} aria-hidden="true" />
              {copy.eyebrow}
            </span>
            <h1>{copy.title}</h1>
            <p>{copy.description}</p>
          </div>

          <div className="browse-head__actions">
            <span className="count-pill">
              {visibleReports.length} {FILTER_LABELS[filter]}
            </span>
            <button
              type="button"
              className="icon-btn"
              onClick={() => onRefresh()}
              disabled={loading}
              aria-label="Refresh reports"
              title="Refresh reports"
            >
              <RefreshCw
                size={16}
                className={loading ? "spin" : undefined}
                aria-hidden="true"
              />
            </button>
            <button
              type="button"
              className="btn btn--primary btn--sm"
              onClick={scrollToForm}
            >
              Report an item
            </button>
          </div>
        </div>

        <div className="trust-bar trust-bar--browse">
          <span className="trust-bar__item">
            <Sparkles size={13} aria-hidden="true" />
            AI match scoring
          </span>
          <span className="trust-bar__item">
            <Search size={13} aria-hidden="true" />
            Compare 7 fields
          </span>
          <span className="trust-bar__item">
            <PackageOpen size={13} aria-hidden="true" />
            Contacts unlock at 70%
          </span>
        </div>
      </div>

      <main className="layout layout--browse">
        <section
          className="panel"
          id="report-form"
          aria-labelledby="report-form-heading"
        >
          <ReportForm
            key={formKey}
            defaultType={initialType}
            user={user}
            onCreated={onCreated}
            onRequireAuth={onRequireAuth}
          />
        </section>

        <section className="reports" aria-labelledby="reports-heading">
          <div className="reports__heading">
            <div>
              <h2 id="reports-heading">{copy.feedTitle}</h2>
              <p>{copy.feedHint}</p>
            </div>

            <div className="reports__heading-actions">
              <span className="count-pill">{counts.all} open</span>
            </div>
          </div>

          <FilterBar
            filter={filter}
            onFilterChange={(value) => onNavigate(routeForFilter(value))}
            query={query}
            onQueryChange={onQueryChange}
            counts={counts}
          />

          {loadError ? (
            <div className="load-error" role="alert">
              <AlertCircle size={20} aria-hidden="true" />
              <div>
                <strong>Could not load reports</strong>
                <p>{loadError}</p>
              </div>
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={() => onRefresh()}
              >
                Retry
              </button>
            </div>
          ) : loading ? (
            <div className="report-list">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : visibleReports.length === 0 ? (
            <EmptyState searching={hasFilters} onReset={resetFilters} />
          ) : (
            <div className="report-list">
              {visibleReports.map((report) => (
                <ReportCard
                  key={report.id}
                  report={report}
                  matchState={matchesByReport[report.id]}
                  signedIn={Boolean(user)}
                  onFindMatches={onFindMatches}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
