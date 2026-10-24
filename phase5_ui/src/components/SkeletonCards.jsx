import React from "react";

export function SkeletonCards() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }} aria-busy="true" aria-label="Loading schemes">
      {[1, 2, 3].map((item) => (
        <div key={item} className="scheme-card glass-panel skeleton-card">
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div className="skeleton-line" style={{ width: "65%", height: "26px" }} />
            <div className="skeleton-line" style={{ width: "15%", height: "26px" }} />
          </div>
          <div className="skeleton-line" style={{ width: "90%", height: "40px" }} />
          <div className="skeleton-line" style={{ width: "40%", height: "20px" }} />
          <div className="skeleton-line" style={{ width: "75%", height: "20px" }} />
          <div className="skeleton-line" style={{ width: "50%", height: "20px" }} />
        </div>
      ))}
    </div>
  );
}
