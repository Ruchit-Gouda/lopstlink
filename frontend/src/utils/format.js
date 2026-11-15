export function formatDate(value) {
  if (!value) return "Unknown date";

  const date = new Date(
    value.length <= 10 ? `${value}T00:00:00` : value,
  );

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function scoreTone(score) {
  if (score >= 70) return "strong";
  if (score >= 45) return "likely";
  return "weak";
}

export function scoreLabel(score) {
  if (score >= 70) return "Strong match";
  if (score >= 45) return "Likely match";
  return "Weak match";
}

export function reportTypeLabel(type) {
  return type === "lost" ? "Lost" : "Found";
}

export function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}
