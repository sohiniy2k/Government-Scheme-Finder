import React from "react";

export function StatTiles({ results, moreSchemes, t }) {
  const allSchemes = [...(results || []), ...(moreSchemes || [])];
  const totalCount = allSchemes.length;

  // Calculate Central vs State counts
  const centralCount = allSchemes.filter(
    (s) => (s.level || "").toLowerCase() === "central"
  ).length;
  const stateCount = totalCount - centralCount;

  // Determine top category from results
  const categoryCounts = {};
  for (const s of results || []) {
    // If the scheme has category tags or matches
    const tags = s.category_tags || [];
    for (const tag of tags) {
      categoryCounts[tag] = (categoryCounts[tag] || 0) + 1;
    }
  }

  let topCategory = "General Welfare";
  let maxCount = 0;
  for (const [cat, cnt] of Object.entries(categoryCounts)) {
    if (cnt > maxCount) {
      maxCount = cnt;
      topCategory = cat;
    }
  }

  return (
    <section className="stat-tiles-grid" aria-label="Schemes summary statistics">
      <div className="stat-tile glass-panel">
        <span className="stat-label">{t.schemesFound}</span>
        <span className="stat-value">{totalCount}</span>
      </div>

      <div className="stat-tile glass-panel">
        <span className="stat-label">{t.centralVsState}</span>
        <span className="stat-value">
          {centralCount} C · {stateCount} S
        </span>
      </div>

      <div className="stat-tile glass-panel">
        <span className="stat-label">{t.topCategory}</span>
        <span className="stat-value" style={{ fontSize: "20px" }}>
          {topCategory}
        </span>
      </div>
    </section>
  );
}
