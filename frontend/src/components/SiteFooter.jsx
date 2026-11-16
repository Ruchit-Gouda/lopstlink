import { HeartHandshake, Link2, Sparkles } from "lucide-react";
import AppLink from "./AppLink";

export default function SiteFooter({ counts, onNavigate }) {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__brand">
          <AppLink to="/" onNavigate={onNavigate} className="brand brand--footer">
            <span className="brand__mark" aria-hidden="true">
              <Link2 size={20} strokeWidth={2.2} />
            </span>
            <span className="brand__text">
              <strong>LostLink</strong>
              <span>Campus lost &amp; found</span>
            </span>
          </AppLink>

          <p>
            A calmer way to reconnect people with the things they lose. Report,
            match and get back to your day.
          </p>

          <div className="site-footer__pills">
            <span>
              <Sparkles size={13} aria-hidden="true" />
              AI match scoring
            </span>
            <span>
              <HeartHandshake size={13} aria-hidden="true" />
              {counts.open} open reports
            </span>
          </div>
        </div>

        <div className="site-footer__columns">
          <div className="site-footer__column">
            <h4>Explore</h4>
            <AppLink to="/" onNavigate={onNavigate}>
              Home
            </AppLink>
            <AppLink to="/browse/lost" onNavigate={onNavigate}>
              Lost reports
            </AppLink>
            <AppLink to="/browse/found" onNavigate={onNavigate}>
              Found reports
            </AppLink>
            <AppLink to="/browse" onNavigate={onNavigate}>
              All reports
            </AppLink>
          </div>

          <div className="site-footer__column">
            <h4>How it works</h4>
            <span>Report with a photo</span>
            <span>We compare every detail</span>
            <span>Contact unlocks at 70%</span>
            <span>Earn 10–15 credits</span>
          </div>
        </div>
      </div>

      <div className="site-footer__base">
        <span>© {new Date().getFullYear()} LostLink</span>
        <span aria-hidden="true">·</span>
        <span>Built for campus communities</span>
      </div>
    </footer>
  );
}
