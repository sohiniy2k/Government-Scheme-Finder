import React from "react";

export function TopBar({ lang, setLang, theme, setTheme, t }) {
  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <header className="top-bar glass-panel" role="banner">
      <div className="top-bar-left">
        <div className="brand-icon" aria-hidden="true">🇮🇳</div>
        <div>
          <h1 className="brand-title">{t.appTitle}</h1>
          <p className="brand-subtitle">{t.appSubtitle}</p>
        </div>
      </div>
      <div className="top-bar-right">
        {/* Language Toggle */}
        <button
          type="button"
          className={`btn-pill ${lang === "en" ? "active" : ""}`}
          onClick={() => setLang("en")}
          aria-label="Switch to English"
        >
          EN
        </button>
        <button
          type="button"
          className={`btn-pill ${lang === "hi" ? "active" : ""}`}
          onClick={() => setLang("hi")}
          aria-label="हिंदी में बदलें"
        >
          हिंदी
        </button>

        {/* Theme Toggle */}
        <button
          type="button"
          className="btn-pill"
          onClick={toggleTheme}
          aria-label="Toggle Dark and Light theme"
          title="Toggle Theme"
        >
          {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
        </button>

        {/* Print Schemes Button */}
        <button
          type="button"
          className="btn-pill"
          onClick={handlePrint}
          aria-label={t.printButton}
          title={t.printButton}
        >
          🖨️ {t.printButton}
        </button>
      </div>
    </header>
  );
}
