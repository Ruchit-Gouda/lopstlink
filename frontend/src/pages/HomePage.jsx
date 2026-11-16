import {
  ArrowRight,
  CalendarDays,
  Coins,
  HeartHandshake,
  ImageOff,
  Inbox,
  MapPin,
  PackageOpen,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import AppLink from "../components/AppLink";
import { formatDate, reportTypeLabel } from "../utils/format";
import { filterReports } from "../utils/reports";

const QUICK_SEARCHES = ["Phone", "Bottle", "Wallet", "ID card"];

const HOW_IT_WORKS = [
  {
    icon: Upload,
    title: "Report it once",
    text: "Add a photo, a short description and the place it was lost or found. It takes under a minute.",
  },
  {
    icon: Sparkles,
    title: "We compare every detail",
    text: "Item name, category, colour, brand, location and date are scored together by the match engine.",
  },
  {
    icon: HeartHandshake,
    title: "Reconnect at 70%+",
    text: "When a pair is strong enough, the reporter sees the other person's contact details and can reach out.",
  },
];

function HeroActivity({ report, onNavigate }) {
  return (
    <AppLink
      to={`/browse/${report.report_type}`}
      onNavigate={onNavigate}
      className="hero-activity"
    >
      <span className="hero-activity__thumb">
        {report.image_url ? (
          <img src={report.image_url} alt="" loading="lazy" />
        ) : (
          <ImageOff size={16} aria-hidden="true" />
        )}
      </span>

      <span className="hero-activity__body">
        <strong>{report.item_name}</strong>
        <span>
          <MapPin size={11} aria-hidden="true" />
          {report.location_text}
        </span>
      </span>

      <span className={`badge badge--${report.report_type} badge--sm`}>
        {reportTypeLabel(report.report_type)}
      </span>
    </AppLink>
  );
}

function HomeReportCard({ report, onNavigate }) {
  return (
    <AppLink
      to={`/browse/${report.report_type}`}
      onNavigate={onNavigate}
      className="home-card"
    >
      <span className="home-card__media">
        {report.image_url ? (
          <img src={report.image_url} alt={report.item_name} loading="lazy" />
        ) : (
          <span className="home-card__placeholder">
            <ImageOff size={24} aria-hidden="true" />
            No photo
          </span>
        )}

        <span className={`badge badge--${report.report_type}`}>
          {reportTypeLabel(report.report_type)}
        </span>
      </span>

      <span className="home-card__body">
        <span className="home-card__title">
          <strong>{report.item_name}</strong>
          <span className="home-card__date">
            <CalendarDays size={12} aria-hidden="true" />
            {formatDate(report.event_date)}
          </span>
        </span>

        <span className="home-card__description">{report.description}</span>

        <span className="home-card__meta">
          <MapPin size={12} aria-hidden="true" />
          {report.location_text}
        </span>

        <span className="home-card__footer">
          <span className={`home-card__dot home-card__dot--${report.report_type}`} />
          {report.category}
          <span className="home-card__open">
            View {report.report_type} reports
            <ArrowRight size={13} aria-hidden="true" />
          </span>
        </span>
      </span>
    </AppLink>
  );
}

function HomeSkeleton() {
  return (
    <div className="home-card home-card--skeleton" aria-hidden="true">
      <span className="skeleton home-card__skeleton-media" />
      <span className="home-card__body">
        <span className="skeleton skeleton--title" />
        <span className="skeleton skeleton--line" />
        <span className="skeleton skeleton--line skeleton--short" />
        <span className="skeleton skeleton--chip" />
      </span>
    </div>
  );
}

export default function HomePage({
  reports,
  loading,
  counts,
  query,
  onQueryChange,
  onNavigate,
  onReport,
}) {
  const normalizedQuery = query.trim();
  const liveResults = normalizedQuery
    ? filterReports(reports, "all", normalizedQuery)
    : [];
  const activity = (reports || []).slice(0, 3);
  const recent = (reports || []).slice(0, 6);

  function handleSearch(event) {
    event.preventDefault();
    onNavigate("/browse");
  }

  return (
    <div className="home">
      <section className="hero" aria-labelledby="hero-heading">
        <div className="hero__glow hero__glow--blue" aria-hidden="true" />
        <div className="hero__glow hero__glow--green" aria-hidden="true" />

        <div className="hero__grid">
          <div className="hero__copy">
            <span className="eyebrow">
              <Sparkles size={14} aria-hidden="true" />
              Smart campus lost &amp; found
            </span>

            <h1 id="hero-heading">
              Lost something?
              <span className="hero__accent">Let&apos;s link it back.</span>
            </h1>

            <p className="hero__lede">
              One calm place for everything your campus loses and finds. Report
              an item, let the match engine compare the details, and reconnect
              when the signal is strong.
            </p>

            <form className="hero-search" onSubmit={handleSearch} role="search">
              <Search size={19} aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                placeholder="Search phones, bottles, wallets, locations…"
                aria-label="Search all reports"
              />
              <button type="submit" className="btn btn--primary">
                Search reports
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </form>

            <div className="hero__suggestions">
              <span>Try</span>
              {QUICK_SEARCHES.map((term) => (
                <button
                  key={term}
                  type="button"
                  onClick={() => onQueryChange(term)}
                >
                  {term}
                </button>
              ))}
            </div>

            {normalizedQuery && (
              <div className="hero-live" aria-live="polite">
                <div className="hero-live__head">
                  <strong>{liveResults.length}</strong>
                  <span>
                    {liveResults.length === 1 ? "report matches" : "reports match"}{" "}
                    &ldquo;{normalizedQuery}&rdquo;
                  </span>
                  <button type="button" onClick={() => onNavigate("/browse")}>
                    View all
                    <ArrowRight size={13} aria-hidden="true" />
                  </button>
                </div>

                {liveResults.length > 0 ? (
                  <div className="hero-live__chips">
                    {liveResults.slice(0, 3).map((report) => (
                      <button
                        key={report.id}
                        type="button"
                        onClick={() =>
                          onNavigate(`/browse/${report.report_type}`)
                        }
                      >
                        {report.item_name}
                        <span>{reportTypeLabel(report.report_type)}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="hero-live__empty">
                    No reports match yet. Try a shorter word or browse
                    everything.
                  </p>
                )}
              </div>
            )}

            <div className="hero__trust">
              <span>
                <ShieldCheck size={14} aria-hidden="true" />
                Contacts unlock at 70%
              </span>
              <span>
                <Coins size={14} aria-hidden="true" />
                Earn 10–15 credits
              </span>
              <span>
                <Sparkles size={14} aria-hidden="true" />
                7-field match engine
              </span>
            </div>
          </div>

          <aside className="hero-board" aria-label="Live community activity">
            <div className="hero-board__head">
              <span className="live-dot" aria-hidden="true" />
              <strong>Live community feed</strong>
              <span className="hero-board__count">{counts.all} open</span>
            </div>

            <div className="hero-board__list">
              {loading ? (
                <div className="hero-board__loading">
                  <span className="skeleton" />
                  <span className="skeleton" />
                  <span className="skeleton" />
                </div>
              ) : activity.length > 0 ? (
                activity.map((report) => (
                  <HeroActivity
                    key={report.id}
                    report={report}
                    onNavigate={onNavigate}
                  />
                ))
              ) : (
                <div className="hero-board__empty">
                  <Sparkles size={20} aria-hidden="true" />
                  <strong>Waiting for the first report</strong>
                  <span>Be the one who starts the chain.</span>
                </div>
              )}
            </div>

            <div className="hero-board__footer">
              <ShieldCheck size={17} aria-hidden="true" />
              <div>
                <strong>Private by design</strong>
                <span>
                  Contact details stay hidden until a strong match is found.
                </span>
              </div>
            </div>
          </aside>
        </div>

        <div className="hero-stats">
          <div className="hero-stat">
            <span className="hero-stat__icon hero-stat__icon--blue">
              <Inbox size={17} aria-hidden="true" />
            </span>
            <div>
              <strong>{counts.all}</strong>
              <span>Open reports</span>
            </div>
          </div>

          <div className="hero-stat">
            <span className="hero-stat__icon hero-stat__icon--amber">
              <Search size={17} aria-hidden="true" />
            </span>
            <div>
              <strong>{counts.lost}</strong>
              <span>Lost items</span>
            </div>
          </div>

          <div className="hero-stat">
            <span className="hero-stat__icon hero-stat__icon--green">
              <PackageOpen size={17} aria-hidden="true" />
            </span>
            <div>
              <strong>{counts.found}</strong>
              <span>Found items</span>
            </div>
          </div>

          <div className="hero-stat">
            <span className="hero-stat__icon hero-stat__icon--violet">
              <HeartHandshake size={17} aria-hidden="true" />
            </span>
            <div>
              <strong>70%</strong>
              <span>Contact unlock</span>
            </div>
          </div>
        </div>
      </section>

      <section
        className="home-section category-section"
        aria-labelledby="categories-heading"
      >
        <div className="section-head">
          <span className="eyebrow">Browse by category</span>
          <h2 id="categories-heading">Start with what you need.</h2>
          <p>
            Lost and found live side by side. Open a category to see every open
            report from the community.
          </p>
        </div>

        <div className="category-grid">
          <AppLink
            to="/browse/lost"
            onNavigate={onNavigate}
            className="category-card category-card--lost"
          >
            <span className="category-card__top">
              <span className="category-card__icon">
                <Search size={22} aria-hidden="true" />
              </span>
              <span className="category-card__count">{counts.lost} open</span>
            </span>

            <h3>Lost items</h3>
            <p>
              Phones, wallets, bottles and everything else that slipped away.
              Find a match or help someone recover theirs.
            </p>

            <span className="category-card__cta">
              Browse lost reports
              <ArrowRight size={16} aria-hidden="true" />
            </span>
          </AppLink>

          <AppLink
            to="/browse/found"
            onNavigate={onNavigate}
            className="category-card category-card--found"
          >
            <span className="category-card__top">
              <span className="category-card__icon">
                <PackageOpen size={22} aria-hidden="true" />
              </span>
              <span className="category-card__count">{counts.found} open</span>
            </span>

            <h3>Found items</h3>
            <p>
              Picked something up? See what the community has found, or publish
              it and earn 15 credits for helping.
            </p>

            <span className="category-card__cta">
              Browse found reports
              <ArrowRight size={16} aria-hidden="true" />
            </span>
          </AppLink>
        </div>
      </section>

      <section className="home-section" aria-labelledby="recent-heading">
        <div className="section-head section-head--row">
          <div>
            <span className="eyebrow">Fresh from the community</span>
            <h2 id="recent-heading">Recent uploads</h2>
            <p>Every report is a chance for something to find its way home.</p>
          </div>

          <AppLink
            to="/browse"
            onNavigate={onNavigate}
            className="section-link"
          >
            View all reports
            <ArrowRight size={15} aria-hidden="true" />
          </AppLink>
        </div>

        {loading ? (
          <div className="home-feed-grid">
            <HomeSkeleton />
            <HomeSkeleton />
            <HomeSkeleton />
          </div>
        ) : recent.length > 0 ? (
          <div className="home-feed-grid">
            {recent.map((report) => (
              <HomeReportCard
                key={report.id}
                report={report}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        ) : (
          <div className="home-empty">
            <span className="home-empty__icon">
              <Inbox size={24} aria-hidden="true" />
            </span>
            <h3>No reports yet</h3>
            <p>
              Be the first to put something on the map. It only takes a minute.
            </p>
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => onReport("lost")}
            >
              Report an item
              <ArrowRight size={15} aria-hidden="true" />
            </button>
          </div>
        )}
      </section>

      <section className="home-section how-section" aria-labelledby="how-heading">
        <div className="section-head section-head--center">
          <span className="eyebrow">How it works</span>
          <h2 id="how-heading">Three steps. One happy reunion.</h2>
          <p>
            No group chats, no endless scrolling. Just a focused place for lost
            and found reports.
          </p>
        </div>

        <div className="how-grid">
          {HOW_IT_WORKS.map((step, index) => {
            const Icon = step.icon;

            return (
              <div className="how-card" key={step.title}>
                <span className="how-card__step">0{index + 1}</span>
                <span className="how-card__icon">
                  <Icon size={20} aria-hidden="true" />
                </span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="home-cta" aria-labelledby="cta-heading">
        <div className="home-cta__glow" aria-hidden="true" />

        <div className="home-cta__copy">
          <span className="eyebrow eyebrow--light">Keep the chain going</span>
          <h2 id="cta-heading">Every report makes the next match possible.</h2>
          <p>
            Found something? Publish it in under a minute, earn 15 credits and
            give someone a very good day.
          </p>
        </div>

        <div className="home-cta__actions">
          <button
            type="button"
            className="btn btn--white"
            onClick={() => onReport("found")}
          >
            <PackageOpen size={16} aria-hidden="true" />
            Report a found item
          </button>
          <button
            type="button"
            className="btn btn--outline-light"
            onClick={() => onReport("lost")}
          >
            <Search size={16} aria-hidden="true" />
            Report a lost item
          </button>
        </div>
      </section>
    </div>
  );
}
