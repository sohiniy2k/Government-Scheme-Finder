import React, { useState, useEffect, useCallback } from "react";
import { translations } from "./i18n/translations";
import { TopBar } from "./components/TopBar";
import { ProfileForm } from "./components/ProfileForm";
import { StatTiles } from "./components/StatTiles";
import { SchemeCard } from "./components/SchemeCard";
import { MoreSchemes } from "./components/MoreSchemes";
import { SchemeDrawer } from "./components/SchemeDrawer";
import { SkeletonCards } from "./components/SkeletonCards";
import "./App.css";

const API_BASE_URL =
  import.meta.env?.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [lang, setLang] = useState("en");
  const [theme, setTheme] = useState("dark");
  const [meta, setMeta] = useState(null);
  const [loadingMeta, setLoadingMeta] = useState(true);

  // User Profile State
  const [profile, setProfile] = useState({
    age: "",
    state: "",
    annual_income: "",
    occupation: "other",
    gender: "prefer_not_to_say",
    social_category: "General",
    disability: false,
    bpl: "unknown",
    interests: [],
    language: "en",
  });

  // Results State
  const [results, setResults] = useState([]);
  const [moreSchemes, setMoreSchemes] = useState([]);
  const [relaxationHint, setRelaxationHint] = useState(null);
  const [disclaimer, setDisclaimer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState(null);

  // Selected scheme for Drawer
  const [selectedSchemeId, setSelectedSchemeId] = useState(null);

  const t = translations[lang] || translations.en;

  // Keep profile language in sync
  useEffect(() => {
    setProfile((prev) => ({ ...prev, language: lang }));
  }, [lang]);

  // Fetch /api/meta on initial mount
  useEffect(() => {
    let isMounted = true;
    setLoadingMeta(true);
    fetch(`${API_BASE_URL}/api/meta`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load metadata");
        return res.json();
      })
      .then((data) => {
        if (isMounted) {
          setMeta(data);
          setLoadingMeta(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Meta fetch error:", err);
          setLoadingMeta(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Handle search submission
  const handleSearch = useCallback(
    async (submittedProfile) => {
      setLoading(true);
      setError(null);
      setHasSearched(true);

      try {
        const payload = {
          ...submittedProfile,
          language: lang,
        };

        const res = await fetch(`${API_BASE_URL}/api/recommend`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}`);
        }

        const data = await res.json();
        setResults(data.results || []);
        setMoreSchemes(data.more_schemes || []);
        setRelaxationHint(data.relaxation_hint || null);
        setDisclaimer(data.disclaimer || null);
      } catch (err) {
        console.error("Recommend error:", err);
        setError(err.message || "Failed to fetch recommendations");
      } finally {
        setLoading(false);
      }
    },
    [lang]
  );

  return (
    <div className="app-container" data-theme={theme}>
      {/* Top Bar Header */}
      <TopBar
        lang={lang}
        setLang={setLang}
        theme={theme}
        setTheme={setTheme}
        t={t}
      />

      {/* Main Dashboard Layout */}
      <main className="dashboard-layout" role="main">
        {/* Left Sidebar Profile Form */}
        <ProfileForm
          meta={meta}
          profile={profile}
          setProfile={setProfile}
          onSubmit={handleSearch}
          loading={loading}
          t={t}
        />

        {/* Right Main Content Area */}
        <section className="main-content" aria-live="polite">
          {/* Stat Tiles (shown when results exist) */}
          {(results.length > 0 || moreSchemes.length > 0) && (
            <StatTiles results={results} moreSchemes={moreSchemes} t={t} />
          )}

          {/* Loading Skeleton */}
          {loading && <SkeletonCards />}

          {/* Error State with Retry Button */}
          {error && !loading && (
            <div className="state-box glass-panel" role="alert">
              <span style={{ fontSize: "36px" }}>⚠️</span>
              <h2 className="state-title">{t.errorTitle}</h2>
              <p className="state-desc">{t.errorMessage}</p>
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleSearch(profile)}
              >
                🔄 {t.retry}
              </button>
            </div>
          )}

          {/* Empty State when zero matches found */}
          {!loading && !error && hasSearched && results.length === 0 && (
            <div className="state-box glass-panel">
              <span style={{ fontSize: "42px" }}>🔍</span>
              <h2 className="state-title">{t.noResultsTitle}</h2>
              <p className="state-desc">{t.noResultsSub}</p>

              {relaxationHint && (
                <div style={{ marginTop: "10px" }}>
                  <span className="relaxation-badge">
                    💡 {t.relaxationHintLabel} {relaxationHint}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Initial Welcome State (before user has searched) */}
          {!loading && !error && !hasSearched && (
            <div className="state-box glass-panel">
              <span style={{ fontSize: "48px" }}>🏛️</span>
              <h2 className="state-title">{t.appTitle}</h2>
              <p className="state-desc">
                Fill in your age, state, and profile on the left panel to
                instantly discover welfare schemes, scholarships, and subsidies
                personalized for you.
              </p>
            </div>
          )}

          {/* Scheme Cards Results */}
          {!loading && !error && results.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {results.map((scheme) => (
                <SchemeCard key={scheme.id} scheme={scheme} t={t} />
              ))}
            </div>
          )}

          {/* More Schemes Compact List */}
          {!loading && !error && moreSchemes.length > 0 && (
            <MoreSchemes
              schemes={moreSchemes}
              onSelectScheme={(id) => setSelectedSchemeId(id)}
              t={t}
            />
          )}
        </section>
      </main>

      {/* Side Drawer for Scheme Details */}
      {selectedSchemeId && (
        <SchemeDrawer
          schemeId={selectedSchemeId}
          onClose={() => setSelectedSchemeId(null)}
          apiUrl={API_BASE_URL}
          t={t}
        />
      )}

      {/* Footer Disclaimer & Trust Badge */}
      <footer className="app-footer" role="contentinfo">
        <p>{disclaimer || t.disclaimerDefault}</p>
        <p style={{ fontWeight: "600", color: "var(--accent-yellow)" }}>
          {t.privacyNotice}
        </p>
      </footer>
    </div>
  );
}
