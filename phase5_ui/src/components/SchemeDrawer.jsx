import React, { useEffect, useState } from "react";

export function SchemeDrawer({ schemeId, onClose, apiUrl, t }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!schemeId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`${apiUrl}/api/schemes/${schemeId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load scheme details");
        return res.json();
      })
      .then((schemeData) => {
        if (isMounted) {
          setData(schemeData);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      isMounted = false;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [schemeId, apiUrl, onClose]);

  if (!schemeId) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label={t.schemeDetails}>
      <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2 style={{ fontSize: "18px", fontWeight: "700" }}>{t.schemeDetails}</h2>
          <button
            type="button"
            className="drawer-close"
            onClick={onClose}
            aria-label={t.close}
          >
            ✕
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "40px" }}>
            <p className="section-content">{t.searching}</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--accent-magenta)" }}>
            <p>{t.errorMessage}</p>
          </div>
        )}

        {data && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
                <span className="badge">{data.level}</span>
                {data.states && (
                  <span className="badge" style={{ borderColor: "var(--accent-yellow)", color: "var(--accent-yellow)" }}>
                    {data.states.join(", ")}
                  </span>
                )}
              </div>
              <h3 style={{ fontSize: "20px", fontWeight: "700", color: "var(--text-primary)" }}>
                {data.name}
              </h3>
            </div>

            {data.benefits && (
              <div className="benefit-highlight">
                <strong>💰 Benefit: </strong> {data.benefits}
              </div>
            )}

            {data.eligibility_text && (
              <div className="card-section">
                <h4 className="section-heading">{t.whyYouQualify}</h4>
                <p className="section-content">{data.eligibility_text}</p>
              </div>
            )}

            {data.documents_required && data.documents_required.length > 0 && (
              <div className="card-section">
                <h4 className="section-heading">{t.documentsNeeded}</h4>
                <ul className="steps-list">
                  {data.documents_required.map((doc, idx) => (
                    <li key={idx}>{doc}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.application_process && data.application_process.length > 0 && (
              <div className="card-section">
                <h4 className="section-heading">{t.howToApply}</h4>
                <ol className="steps-list">
                  {data.application_process.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </div>
            )}

            {data.official_url && (
              <div style={{ marginTop: "12px" }}>
                <a
                  href={data.official_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ display: "inline-flex", width: "100%", justifyContent: "center" }}
                >
                  🏛️ {t.officialSite} ↗
                </a>
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
