import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Coins,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import "./App.css";
import {
  createReport,
  fetchMatches,
  fetchMe,
  fetchReports,
  getSession,
  logout as endSession,
} from "./api";
import AuthDialog from "./components/AuthDialog";
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
  const [notice, setNotice] = useState(null);
  const [user, setUser] = useState(() => getSession()?.user ?? null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");

  const showNotice = useCallback((type, text) => {
    setNotice({ type, text });
  }, []);

  useEffect(() => {
    if (!notice) return undefined;

    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    if (!getSession()) return undefined;

    let active = true;

    fetchMe()
      .then((profile) => {
        if (active && profile) setUser(profile);
      })
      .catch((error) => {
        if (!active) return;
        if (error.status === 401 || error.status === 403) {
          endSession();
          setUser(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

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

  function openAuth(mode = "login") {
    setAuthMode(mode);
    setAuthOpen(true);
  }

  function handleAuthenticated(profile, mode) {
    setUser(profile);
    setAuthOpen(false);
    setMatchesByReport({});

    const firstName = (profile.full_name || "there").split(" ")[0];

    showNotice(
      "success",
      mode === "signup"
        ? `Welcome to LostLink, ${firstName}!`
        : `Welcome back, ${firstName}!`,
    );
  }

  function handleLogout() {
    endSession();
    setUser(null);
    setMatchesByReport({});
    showNotice("success", "You have been logged out.");
  }

  async function handleCreate(formData) {
    const data = await createReport(formData);

    if (data.user) setUser(data.user);

    const awarded = data.credits?.awarded || 0;
    const total = data.credits?.total || 0;

    showNotice(
      "success",
      awarded > 0
        ? `Report published · +${awarded} credits (${total} total)`
        : "Report published. We'll start looking for matches.",
    );

    await loadReports({ silent: true });
    return data;
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
        [reportId]: {
          status: "ready",
          data: data.matches || [],
          threshold: data.contact_threshold ?? 70,
          viewerIsOwner: Boolean(data.viewer_is_owner),
        },
      }));
    } catch (error) {
      setMatchesByReport((previous) => ({
        ...previous,
        [reportId]: { status: "error", error: error.message },
      }));
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
        user={user}
        onLogin={() => openAuth("login")}
        onLogout={handleLogout}
      />

      <div className="trust-bar">
        <span className="trust-bar__item">
          <Sparkles size={13} aria-hidden="true" />
          AI match scoring
        </span>
        <span className="trust-bar__item">
          <ShieldCheck size={13} aria-hidden="true" />
          Contacts unlock at 70%
        </span>
        <span className="trust-bar__item">
          <Coins size={13} aria-hidden="true" />
          Earn credits for every report
        </span>
      </div>

      <main className="layout">
        <section className="panel" aria-labelledby="report-form-heading">
          <ReportForm
            user={user}
            onCreated={handleCreate}
            onRequireAuth={() => openAuth("login")}
          />
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
                  signedIn={Boolean(user)}
                  onFindMatches={handleFindMatches}
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

      {authOpen && (
        <AuthDialog
          key={authMode}
          mode={authMode}
          onClose={() => setAuthOpen(false)}
          onAuthenticated={handleAuthenticated}
        />
      )}

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
