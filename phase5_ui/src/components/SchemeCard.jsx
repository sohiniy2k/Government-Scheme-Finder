import React, { useState } from "react";

export function SchemeCard({ scheme, t }) {
  const [checkedDocs, setCheckedDocs] = useState({});

  const toggleDoc = (idx) => {
    setCheckedDocs((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const isCentral = (scheme.level || "").toLowerCase() === "central";
  const sourceLabel =
    scheme.source === "llm" ? t.aiExplained : t.basicInfo;

  return (
    <article className="scheme-card glass-panel" aria-labelledby={`scheme-${scheme.id}`}>
      <header className="scheme-header">
        <div>
          <h2 id={`scheme-${scheme.id}`} className="scheme-title">
            {scheme.name}
          </h2>
          {scheme.summary && (
            <p className="section-content" style={{ marginTop: "6px" }}>
              {scheme.summary}
            </p>
          )}
        </div>
        <div className="badge-group">
          <span className="badge" title={isCentral ? "Central Government" : "State Government"}>
            {isCentral ? t.centralVsState.split(" ")[0] : t.centralVsState.split(" ")[2] || scheme.level}
          </span>
          <span className="badge badge-source">{sourceLabel}</span>
        </div>
      </header>

      {/* Benefit Highlight */}
      {scheme.benefits && (
        <div className="benefit-highlight">
          <strong>💰 Benefit: </strong> {scheme.benefits}
        </div>
      )}

      {/* Why You Qualify */}
      {scheme.why_you_qualify && (
        <div className="card-section">
          <h3 className="section-heading">{t.whyYouQualify}</h3>
          <p className="section-content">{scheme.why_you_qualify}</p>
        </div>
      )}

      {/* Conditions / Things to Check */}
      {scheme.things_to_check && scheme.things_to_check.length > 0 && (
        <div className="card-section">
          <h3 className="section-heading">{t.thingsToCheck}</h3>
          <ul className="steps-list">
            {scheme.things_to_check.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Documents Needed as Interactive Checklist */}
      {scheme.documents_needed && scheme.documents_needed.length > 0 && (
        <div className="card-section">
          <h3 className="section-heading">{t.documentsNeeded}</h3>
          <ul className="doc-checklist">
            {scheme.documents_needed.map((doc, idx) => {
              const isChecked = !!checkedDocs[idx];
              return (
                <li key={idx}>
                  <label className={`doc-item ${isChecked ? "checked" : ""}`}>
                    <input
                      type="checkbox"
                      className="doc-checkbox"
                      checked={isChecked}
                      onChange={() => toggleDoc(idx)}
                      aria-label={doc}
                    />
                    <span>{doc}</span>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* How to Apply */}
      {scheme.how_to_apply && scheme.how_to_apply.length > 0 && (
        <div className="card-section">
          <h3 className="section-heading">{t.howToApply}</h3>
          <ol className="steps-list">
            {scheme.how_to_apply.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Official site link */}
      {scheme.official_url && (
        <footer className="card-footer">
          <a
            href={scheme.official_url}
            target="_blank"
            rel="noopener noreferrer"
            className="link-btn"
            aria-label={`Visit official site for ${scheme.name}`}
          >
            🏛️ {t.officialSite} ↗
          </a>
        </footer>
      )}
    </article>
  );
}
