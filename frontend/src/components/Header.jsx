import { Coins, Link2, LogIn, LogOut } from "lucide-react";
import AppLink from "./AppLink";

function initials(name, email) {
  const source = (name || email || "?").trim();
  const parts = source.split(/\s+/).filter(Boolean);

  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
}

export default function Header({
  counts,
  user,
  route,
  onLogin,
  onLogout,
  onNavigate,
}) {
  const isHome = route?.name === "home";
  const isBrowse = route?.name === "browse";
  const isLost = isBrowse && route.filter === "lost";
  const isFound = isBrowse && route.filter === "found";
  const isAll = isBrowse && route.filter === "all";

  const links = [
    { label: "Home", to: "/", active: isHome },
    { label: "Lost", to: "/browse/lost", active: isLost },
    { label: "Found", to: "/browse/found", active: isFound },
    { label: "Browse", to: "/browse", active: isAll },
  ];

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <AppLink
          to="/"
          onNavigate={onNavigate}
          className="brand"
          aria-label="LostLink home"
        >
          <span className="brand__mark" aria-hidden="true">
            <Link2 size={22} strokeWidth={2.2} />
          </span>
          <span className="brand__text">
            <strong>LostLink</strong>
            <span>Campus lost &amp; found</span>
          </span>
        </AppLink>

        <nav className="site-nav" aria-label="Primary navigation">
          {links.map((link) => (
            <AppLink
              key={link.to}
              to={link.to}
              onNavigate={onNavigate}
              className={`site-nav__link${link.active ? " is-active" : ""}`}
              aria-current={link.active ? "page" : undefined}
            >
              {link.label}
            </AppLink>
          ))}
        </nav>

        <div className="header-right">
          <div className="header-stats" aria-label="Open report statistics">
            <div className="stat">
              <span className="stat__value">{counts.open}</span>
              <span className="stat__label">Open</span>
            </div>
            <div className="stat">
              <span className="stat__value">{counts.lost}</span>
              <span className="stat__label">Lost</span>
            </div>
            <div className="stat">
              <span className="stat__value">{counts.found}</span>
              <span className="stat__label">Found</span>
            </div>
          </div>

          {user ? (
            <div className="header-user">
              <span
                className="credits-chip"
                title="Earn 10 credits for a lost report and 15 for a found report"
              >
                <Coins size={15} aria-hidden="true" />
                <strong>{user.points ?? 0}</strong>
                <span>credits</span>
              </span>

              <span className="header-user__identity">
                <span className="header-user__name">
                  {user.full_name || "LostLink member"}
                </span>
                <span className="header-user__email">{user.email}</span>
              </span>

              <span
                className="user-avatar"
                title={user.full_name || user.email}
                aria-hidden="true"
              >
                {initials(user.full_name, user.email)}
              </span>

              <button
                type="button"
                className="icon-btn"
                onClick={onLogout}
                aria-label="Log out"
                title="Log out"
              >
                <LogOut size={16} aria-hidden="true" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn--primary btn--sm header-login"
              onClick={onLogin}
            >
              <LogIn size={15} aria-hidden="true" />
              Log in
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
