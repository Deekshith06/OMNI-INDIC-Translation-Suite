"use client";

import React from "react";

/* ─── Component ────────────────────────────────────────────────────── */

interface ConfidenceBarProps {
  score: number; // 0.0 to 1.0
}

export default function ConfidenceBar({ score }: ConfidenceBarProps) {
  const percentage = Math.round(score * 100);

  // Color based on confidence level
  let color: string;
  let label: string;
  if (percentage >= 80) {
    color = "var(--success)";
    label = "High Confidence";
  } else if (percentage >= 50) {
    color = "var(--warning)";
    label = "Moderate Confidence";
  } else {
    color = "var(--error)";
    label = "Low Confidence";
  }

  return (
    <div id="confidence-bar" className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: color }}
        />
        <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
          {label}
        </span>
      </div>
      <div className="flex-1 flex items-center gap-2">
        <div
          className="flex-1 h-1.5 rounded-full overflow-hidden"
          style={{ background: "var(--bg-primary)" }}
        >
          <div
            className="h-full rounded-full"
            style={{
              width: `${percentage}%`,
              background: color,
              transition: "width 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
              animation: "progress-fill 0.8s ease-out",
            }}
          />
        </div>
        <span
          className="text-xs font-bold tabular-nums"
          style={{ color, minWidth: "36px", textAlign: "right" }}
        >
          {percentage}%
        </span>
      </div>
    </div>
  );
}
