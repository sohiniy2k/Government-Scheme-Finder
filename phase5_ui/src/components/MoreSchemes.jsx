import React from "react";

export function MoreSchemes({ schemes, onSelectScheme, t }) {
  if (!schemes || schemes.length === 0) return null;

  return (
    <section className="more-schemes-section" aria-labelledby="more-schemes-title">
      <div>
        <h3 id="more-schemes-title" className="section-heading" style={{ fontSize: "18px" }}>
          {t.moreSchemesTitle}
        </h3>
        <p className="section-content" style={{ fontSize: "14px", marginTop: "2px" }}>
          {t.moreSchemesSubtitle}
        </p>
      </div>

      <div className="more-schemes-grid">
        {schemes.map((scheme) => (
          <div
            key={scheme.id}
            className="compact-scheme-card glass-panel"
            onClick={() => onSelectScheme(scheme.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectScheme(scheme.id);
              }
            }}
            aria-label={`${scheme.name} - ${t.viewDetails}`}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span className="badge" style={{ fontSize: "10px" }}>
                  {scheme.level}
                </span>
              </div>
              <h4 className="compact-title">{scheme.name}</h4>
              {scheme.benefits && (
                <p className="compact-benefit">{scheme.benefits}</p>
              )}
            </div>

            <span style={{ fontSize: "13px", color: "var(--accent-yellow)", fontWeight: "600" }}>
              {t.viewDetails} →
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
