// Empty by default so the app calls relative "/api/..." paths. In local
// development Vite proxies those to the backend; in production set
// VITE_API_URL to the deployed backend origin.
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

const SESSION_KEY = "lostlink.session.v1";

function loadSession() {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.access_token || !parsed?.refresh_token) return null;
    return parsed;
  } catch {
    return null;
  }
}

let cachedSession = loadSession();

function persistSession() {
  try {
    if (cachedSession) {
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(cachedSession));
    } else {
      window.localStorage.removeItem(SESSION_KEY);
    }
  } catch {
    // Storage can be unavailable in private browsing; the in-memory session
    // still works for the current tab.
  }
}

export function getSession() {
  return cachedSession;
}

export function setSession(session, user) {
  if (!session?.access_token) return null;

  const expiresAt = session.expires_in
    ? Date.now() + Number(session.expires_in) * 1000
    : null;

  cachedSession = {
    access_token: session.access_token,
    refresh_token: session.refresh_token || cachedSession?.refresh_token || "",
    expires_at: expiresAt,
    user: user ?? cachedSession?.user ?? null,
  };

  persistSession();
  return cachedSession;
}

export function updateSessionUser(user) {
  if (!cachedSession) return;
  cachedSession = { ...cachedSession, user };
  persistSession();
}

export function clearSession() {
  cachedSession = null;
  persistSession();
}

function errorMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || "Invalid value")
      .join(". ");
  }
  return `Request failed (${status})`;
}

async function refreshTokens() {
  const refreshToken = cachedSession?.refresh_token;
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearSession();
      return false;
    }

    const data = await response.json();
    setSession(data.session, data.user);
    return true;
  } catch {
    return false;
  }
}

async function request(path, options = {}, config = {}) {
  const { auth = false, retry = true } = config;
  const headers = new Headers(options.headers || {});

  if (auth && cachedSession?.access_token) {
    headers.set("Authorization", `Bearer ${cachedSession.access_token}`);
  }

  let response;

  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    const error = new Error(
      "Cannot reach the server. Please check your connection.",
    );
    error.status = 0;
    throw error;
  }

  if (response.status === 401 && auth && retry && cachedSession?.refresh_token) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      return request(path, options, { auth, retry: false });
    }
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Some error responses have no JSON body.
  }

  if (!response.ok) {
    const error = new Error(errorMessage(data, response.status));
    error.status = response.status;
    throw error;
  }

  return data;
}

export function fetchReports() {
  return request("/api/reports");
}

export function createReport(formData) {
  return request("/api/reports", { method: "POST", body: formData }, { auth: true }).then(
    (data) => {
      if (data?.user) updateSessionUser(data.user);
      return data;
    },
  );
}

export function fetchMatches(reportId, minScore = 25) {
  return request(
    `/api/matches/${reportId}?min_score=${minScore}`,
    {},
    { auth: Boolean(cachedSession?.access_token) },
  );
}

export async function signup(payload) {
  const data = await request("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  setSession(data.session, data.user);
  return data.user;
}

export async function login(payload) {
  const data = await request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  setSession(data.session, data.user);
  return data.user;
}

export async function fetchMe() {
  const data = await request("/api/auth/me", {}, { auth: true });
  if (data?.user) updateSessionUser(data.user);
  return data.user;
}

export function logout() {
  clearSession();
}

export { API_URL };
