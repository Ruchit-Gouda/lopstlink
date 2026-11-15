import { Search, X } from "lucide-react";

const FILTERS = [
  { value: "all", label: "All" },
  { value: "lost", label: "Lost" },
  { value: "found", label: "Found" },
];

export default function FilterBar({
  filter,
  onFilterChange,
  query,
  onQueryChange,
  counts,
}) {
  return (
    <div className="toolbar">
      <div className="search">
        <Search size={17} aria-hidden="true" />
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search items, colors, locations…"
          aria-label="Search reports"
        />
        {query && (
          <button
            type="button"
            className="search__clear"
            onClick={() => onQueryChange("")}
            aria-label="Clear search"
          >
            <X size={15} aria-hidden="true" />
          </button>
        )}
      </div>

      <div className="segmented" role="group" aria-label="Filter by report type">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            type="button"
            className={`segmented__btn${
              filter === item.value ? " is-active" : ""
            }`}
            aria-pressed={filter === item.value}
            onClick={() => onFilterChange(item.value)}
          >
            {item.label}
            <span className="segmented__count">{counts[item.value]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
