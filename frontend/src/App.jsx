import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, X } from "lucide-react";
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
import Header from "./components/Header";
import SiteFooter from "./components/SiteFooter";
import BrowsePage from "./pages/BrowsePage";
import HomePage from "./pages/HomePage";
import { parseRoute } from "./router";

const MIN_SCORE = 25;

export default function App() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [query, setQuery] = useState("");
  const [route, setRoute] = useState(() => parseRoute());
  const [matchesByReport, setMatchesByReport] = useState({});
  const [notice, setNotice] = useState(null);
  const [user, setUser] = useState(() => getSession()?.user ?? null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [formRequest, setFormRequest] = useState({ type: "lost", key: 0 });

  const showNotice = useCallback((type, text) => {
    setNotice({ type, text });
  }, []);

  useEffect(() => {
    if (!notice) return undefined;

    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    function handlePopState() {
      setRoute(parseRoute());
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [route.path]);

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

  const navigate = useCallback((path) => {
    if (!path) return;

    const nextRoute = parseRoute(path);

    if (path !== `${window.location.pathname}${window.location.search}`) {
      window.history.pushState({}, "", path);
    }

    setRoute(nextRoute);
  }, []);

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

  function handleReport(type) {
    const reportType = type === "found" ? "found" : "lost";

    setFormRequest((previous) => ({
      type: reportType,
      key: previous.key + 1,
    }));

    navigate("/browse");

    window.setTimeout(() => {
      document
        .getElementById("report-form")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 120);
  }

  const isHome = route.name === "home";

  return (
    <div className="app">
      <Header
        counts={{ open: counts.all, lost: counts.lost, found: counts.found }}
        user={user}
        route={route}
        onLogin={() => openAuth("login")}
        onLogout={handleLogout}
        onNavigate={navigate}
      />

      {isHome ? (
        <HomePage
          reports={reports}
          loading={loading}
          counts={counts}
          query={query}
          onQueryChange={setQuery}
          onNavigate={navigate}
          onReport={handleReport}
        />
      ) : (
        <BrowsePage
          route={route}
          counts={counts}
          reports={reports}
          loading={loading}
          loadError={loadError}
          onRefresh={loadReports}
          user={user}
          onRequireAuth={() => openAuth("login")}
          onCreated={handleCreate}
          matchesByReport={matchesByReport}
          onFindMatches={handleFindMatches}
          query={query}
          onQueryChange={setQuery}
          onNavigate={navigate}
          initialType={formRequest.type}
          formKey={formRequest.key}
        />
      )}

      <SiteFooter counts={counts} onNavigate={navigate} />

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
