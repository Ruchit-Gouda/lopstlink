import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  X,
} from "lucide-react";
import "./App.css";
import { createReport, fetchMatches, fetchReports, updateReportStatus } from "./api";
import ConfirmDialog from "./components/ConfirmDialog";
import EmptyState from "./components/EmptyState";
import FilterBar from "./components/FilterBar";
import Header from "./components/Header";
import ReportCard from "./components/ReportCard";
import ReportForm from "./components/ReportForm";
import SkeletonCard from "./components/SkeletonCard";

const MIN_SCORE = 25;

function matchesFilter(report, filter, query) {
  if (filter !== "all" && report.report_type !== filter) return false;
  if (!query) return true;

  const haystack = [
    report.item_name,
    report.category,
    report.description,
    report.color,
    report.brand,
    report.location_text,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(query);
}

export default function App() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [matchesByReport, setMatchesByReport] = useState({});
  const [resolvingId, setResolvingId] = useState(null);
  const [pendingResolve, setPendingResolve] = useState(null);
  const [notice, setNotice] = useState(null);

  const showNotice = useCallback((type, text) => {
    setNotice({ type, text });
  }, []);

  useEffect(() => {
    if (!notice) return undefined;

    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const loadReports = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true);
    setLoadError("");

    try {
      const data = await fetchReports();
      setReports(data.reports || []);
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const counts = useMemo(
    () => ({
      all: reports.length,
      lost: reports.filter((report) => report.report_type === "lost").length,
      found: reports.filter((report) => report.report_type === "found").length,
    }),
    [reports],
  );

  const normalizedQuery = query.trim().toLowerCase();

  const visibleReports = useMemo(
    () =>
      reports.filter((report) =>
        matchesFilter(report, filter, normalizedQuery),
      ),
    [reports, filter, normalizedQuery],
  );

  const hasFilters = filter !== "all" || normalizedQuery.length > 0;

  async function handleCreate(formData) {
    await createReport(formData);
    showNotice("success", "Report submitted. We'll start looking for matches.");
    await loadReports({ silent: true });
  }

  async function handleFindMatches(reportId) {
    setMatchesByReport((previous) => ({
      ...previous,
      [reportId]: { status: "loading" },
    }));

    try {
      const data = await fetchMatches(reportId, MIN_SCORE);
      setMatchesByReport((previous) => ({
        ...previous,
        [reportId]: { status: "ready", data: data.matches || [] },
      }));
    } catch (error) {
      setMatchesByReport((previous) => ({
        ...previous,
        [reportId]: { status: "error", error: error.message },
      }));
    }
  }

  function handleResolve(report) {
    setPendingResolve(report);
  }

  const cancelResolve = useCallback(() => {
    setPendingResolve(null);
  }, []);

  async function confirmResolve() {
    const report = pendingResolve;
    if (!report) return;

    setResolvingId(report.id);

    try {
      await updateReportStatus(report.id, "resolved");
      setReports((previous) =>
        previous.filter((item) => item.id !== report.id),
      );
      setMatchesByReport((previous) => {
        const next = { ...previous };
        delete next[report.id];
        return next;
      });
      showNotice("success", `"${report.item_name}" marked as resolved.`);
    } catch (error) {
      showNotice("error", error.message);
    } finally {
      setResolvingId(null);
      setPendingResolve(null);
    }
  }

  function resetFilters() {
    setFilter("all");
    setQuery("");
  }

  return (
    <div className="app">
      <Header
        counts={{ open: counts.all, lost: counts.lost, found: counts.found }}
      />

      <main className="layout">
        <section className="panel" aria-labelledby="report-form-heading">
          <ReportForm onCreated={handleCreate} onNotice={showNotice} />
        </section>

        <section className="reports" aria-labelledby="reports-heading">
          <div className="reports__heading">
            <div>
              <h2 id="reports-heading">Community reports</h2>
              <p>Browse open reports or search for a possible match.</p>
            </div>

            <div className="reports__heading-actions">
              <span className="count-pill">{counts.all} open</span>
              <button
                type="button"
                className="icon-btn"
                onClick={() => loadReports()}
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
            </div>
          </div>

          <FilterBar
            filter={filter}
            onFilterChange={setFilter}
            query={query}
            onQueryChange={setQuery}
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
                onClick={() => loadReports()}
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
                  onFindMatches={handleFindMatches}
                  onResolve={handleResolve}
                  resolving={resolvingId === report.id}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="site-footer">
        <span>LostLink</span>
        <span aria-hidden="true">·</span>
        <span>Campus lost &amp; found, matched intelligently</span>
      </footer>

      <ConfirmDialog
        open={Boolean(pendingResolve)}
        title="Mark this report as resolved?"
        description={
          pendingResolve
            ? `"${pendingResolve.item_name}" will be removed from the open reports list. You can open it again from the database if needed.`
            : ""
        }
        confirmLabel="Mark resolved"
        busy={Boolean(resolvingId)}
        onCancel={cancelResolve}
        onConfirm={confirmResolve}
      />

      {notice && (
        <div
          className={`toast toast--${notice.type}`}
          role="status"
          aria-live="polite"
        >
          {notice.type === "success" ? (
            <CheckCircle2 size={18} aria-hidden="true" />
          ) : (
            <AlertCircle size={18} aria-hidden="true" />
          )}
          <span>{notice.text}</span>
          <button
            type="button"
            className="toast__close"
            onClick={() => setNotice(null)}
            aria-label="Dismiss notification"
          >
            <X size={15} aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  );
}
