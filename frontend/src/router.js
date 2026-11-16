const ROUTES = {
  "/": { name: "home", filter: "all", path: "/" },
  "/browse": { name: "browse", filter: "all", path: "/browse" },
  "/browse/lost": { name: "browse", filter: "lost", path: "/browse/lost" },
  "/browse/found": { name: "browse", filter: "found", path: "/browse/found" },
};

export function parseRoute(pathname = window.location.pathname) {
  const clean = (pathname || "/").split("?")[0].split("#")[0];
  const normalized = clean.length > 1 ? clean.replace(/\/+$/, "") : clean;

  return ROUTES[normalized] || ROUTES["/"];
}

export function routeForFilter(filter) {
  if (filter === "lost") return "/browse/lost";
  if (filter === "found") return "/browse/found";
  return "/browse";
}

export function shouldHandleLink(event) {
  return (
    !event.defaultPrevented &&
    event.button === 0 &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.altKey
  );
}
