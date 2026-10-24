import React, { useState } from "react";
import { Tooltip } from "./Tooltip";

export function ProfileForm({
  meta,
  profile,
  setProfile,
  onSubmit,
  loading,
  t,
}) {
  const [errors, setErrors] = useState({});
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const states = meta?.states || [];
  const occupations = meta?.occupations || [];
  const genders = meta?.genders || [];
  const socialCategories = meta?.social_categories || [];
  const bplOptions = meta?.bpl || [];
  const availableInterests = meta?.interests || [];

  const handleInputChange = (field, value) => {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  const toggleInterest = (interest) => {
    setProfile((prev) => {
      const current = prev.interests || [];
      const exists = current.includes(interest);
      const updated = exists
        ? current.filter((item) => item !== interest)
        : [...current, interest];
      return { ...prev, interests: updated };
    });
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};

    // Validation blocks empty age / state
    if (profile.age === "" || profile.age === null || profile.age === undefined) {
      newErrors.age = t.age + " is required";
    } else {
      const parsedAge = Number(profile.age);
      if (isNaN(parsedAge) || parsedAge < 0 || parsedAge > 120) {
        newErrors.age = "Age must be between 0 and 120";
      }
    }

    if (!profile.state || profile.state.trim() === "") {
      newErrors.state = t.state + " is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Submit validated payload
    onSubmit({
      ...profile,
      age: Number(profile.age),
      annual_income: Number(profile.annual_income || 0),
    });
  };

  return (
    <aside className="sidebar glass-panel" aria-label={t.citizenProfile}>
      <div className="sidebar-header">
        <h2 className="sidebar-title">{t.citizenProfile}</h2>
        <button
          type="button"
          className="btn-pill"
          style={{ display: "none" }} /* Shown via media query in small screens if needed */
          onClick={() => setIsMobileOpen(!isMobileOpen)}
        >
          {t.toggleFilters}
        </button>
      </div>

      <form onSubmit={handleFormSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Age Input */}
        <div className="form-group">
          <label htmlFor="input-age" className="form-label">
            {t.age} <span style={{ color: "var(--accent-magenta)" }}>*</span>
          </label>
          <input
            id="input-age"
            name="age"
            type="number"
            min={0}
            max={120}
            className="form-input"
            placeholder={t.agePlaceholder}
            value={profile.age ?? ""}
            onChange={(e) => handleInputChange("age", e.target.value)}
            required
            aria-invalid={!!errors.age}
            aria-describedby={errors.age ? "error-age" : undefined}
          />
          {errors.age && (
            <span id="error-age" style={{ color: "var(--accent-magenta)", fontSize: "12px", fontWeight: "600" }}>
              {errors.age}
            </span>
          )}
        </div>

        {/* State Dropdown */}
        <div className="form-group">
          <label htmlFor="select-state" className="form-label">
            {t.state} <span style={{ color: "var(--accent-magenta)" }}>*</span>
          </label>
          <select
            id="select-state"
            name="state"
            className="form-select"
            value={profile.state || ""}
            onChange={(e) => handleInputChange("state", e.target.value)}
            required
            aria-invalid={!!errors.state}
            aria-describedby={errors.state ? "error-state" : undefined}
          >
            <option value="">-- {t.selectState} --</option>
            {states.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
          {errors.state && (
            <span id="error-state" style={{ color: "var(--accent-magenta)", fontSize: "12px", fontWeight: "600" }}>
              {errors.state}
            </span>
          )}
        </div>

        {/* Annual Income Input */}
        <div className="form-group">
          <label htmlFor="input-income" className="form-label">
            {t.annualIncome}
          </label>
          <input
            id="input-income"
            name="annual_income"
            type="number"
            min={0}
            step={1000}
            className="form-input"
            placeholder={t.incomePlaceholder}
            value={profile.annual_income ?? ""}
            onChange={(e) => handleInputChange("annual_income", e.target.value)}
          />
        </div>

        {/* Occupation Dropdown */}
        <div className="form-group">
          <label htmlFor="select-occupation" className="form-label">
            {t.occupation}
          </label>
          <select
            id="select-occupation"
            name="occupation"
            className="form-select"
            value={profile.occupation || "other"}
            onChange={(e) => handleInputChange("occupation", e.target.value)}
          >
            {occupations.map((occ) => (
              <option key={occ} value={occ}>
                {occ.replace("_", " ").toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Gender Dropdown */}
        <div className="form-group">
          <label htmlFor="select-gender" className="form-label">
            {t.gender}
          </label>
          <select
            id="select-gender"
            name="gender"
            className="form-select"
            value={profile.gender || "prefer_not_to_say"}
            onChange={(e) => handleInputChange("gender", e.target.value)}
          >
            {genders.map((gen) => (
              <option key={gen} value={gen}>
                {gen.replace("_", " ").toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Social Category Dropdown with Tooltips */}
        <div className="form-group">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label htmlFor="select-social-category" className="form-label">
              {t.socialCategory}
            </label>
            <div style={{ display: "flex", gap: "6px" }}>
              <Tooltip text={t.casteTooltip} />
              <Tooltip text={t.ewsTooltip} />
            </div>
          </div>
          <select
            id="select-social-category"
            name="social_category"
            className="form-select"
            value={profile.social_category || "General"}
            onChange={(e) => handleInputChange("social_category", e.target.value)}
          >
            {socialCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* BPL Dropdown with Tooltip */}
        <div className="form-group">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label htmlFor="select-bpl" className="form-label">
              {t.bpl}
            </label>
            <Tooltip text={t.bplTooltip} />
          </div>
          <select
            id="select-bpl"
            name="bpl"
            className="form-select"
            value={profile.bpl || "unknown"}
            onChange={(e) => handleInputChange("bpl", e.target.value)}
          >
            {bplOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Disability Checkbox */}
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="disability"
              className="checkbox-input"
              checked={!!profile.disability}
              onChange={(e) => handleInputChange("disability", e.target.checked)}
            />
            <span>{t.disability}</span>
          </label>
        </div>

        {/* Interests Selectable Chips */}
        {availableInterests.length > 0 && (
          <div className="form-group">
            <label className="form-label">{t.interests}</label>
            <div className="chips-container" role="group" aria-label={t.interests}>
              {availableInterests.map((interest) => {
                const isActive = (profile.interests || []).includes(interest);
                return (
                  <button
                    key={interest}
                    type="button"
                    className={`chip ${isActive ? "active" : ""}`}
                    onClick={() => toggleInterest(interest)}
                    aria-pressed={isActive}
                  >
                    {isActive ? "✓ " : "+ "}
                    {interest}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? t.searching : `🔍 ${t.findSchemes}`}
        </button>
      </form>
    </aside>
  );
}
