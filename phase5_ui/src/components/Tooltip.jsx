import React from "react";

export function Tooltip({ text }) {
  return (
    <span className="tooltip-wrap" tabIndex={0} aria-label={text}>
      <span className="tooltip-icon" aria-hidden="true">?</span>
      <span className="tooltip-text" role="tooltip">{text}</span>
    </span>
  );
}
