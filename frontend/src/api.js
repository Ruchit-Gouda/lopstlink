// Empty by default so the app calls relative "/api/..." paths. In local
// development Vite proxies those to the backend; in production set
// VITE_API_URL to the deployed backend origin.
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

function errorMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || "Invalid value")
      .join(". ");
  }
  return `Request failed (${status})`;
}

async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Please check your connection.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Some error responses have no JSON body.
  }

  if (!response.ok) {
    throw new Error(errorMessage(data, response.status));
  }

  return data;
}

export function fetchReports() {
  return request("/api/reports");
}

export function createReport(formData) {
  return request("/api/reports", {
    method: "POST",
    body: formData,
  });
}

export function fetchMatches(reportId, minScore = 25) {
  return request(`/api/matches/${reportId}?min_score=${minScore}`);
}

export function updateReportStatus(reportId, status) {
  return request(`/api/reports/${reportId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export { API_URL };
