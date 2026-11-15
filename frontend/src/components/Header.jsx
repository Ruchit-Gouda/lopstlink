import { Link2 } from "lucide-react";

export default function Header({ counts }) {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a className="brand" href="/" aria-label="LostLink home">
          <span className="brand__mark" aria-hidden="true">
            <Link2 size={22} strokeWidth={2.2} />
          </span>
          <span className="brand__text">
            <strong>LostLink</strong>
            <span>Campus lost &amp; found</span>
          </span>
        </a>

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
      </div>
    </header>
  );
}
