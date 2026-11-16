export function matchesReport(report, filter = "all", query = "") {
  if (!report) return false;
  if (filter !== "all" && report.report_type !== filter) return false;

  const normalized = (query || "").trim().toLowerCase();
  if (!normalized) return true;

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

  return normalized
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => haystack.includes(term));
}

export function filterReports(reports, filter = "all", query = "") {
  return (reports || []).filter((report) =>
    matchesReport(report, filter, query),
  );
}

export function recentReports(reports, limit = 6) {
  return (reports || []).slice(0, limit);
}
