"use client";

import React from "react";
import type { TranslationMode } from "@/types";

interface TransliterationToggleProps {
  mode: TranslationMode;
  onChange: (mode: TranslationMode) => void;
}

export default function TransliterationToggle({ mode, onChange }: TransliterationToggleProps) {
  return (
    <div className="toggle-group">
      <button
        id="mode-translate"
        className={`toggle-option ${mode === "translate" ? "active" : ""}`}
        onClick={() => onChange("translate")}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
        </svg>
        Translate
      </button>
      <button
        id="mode-transliterate"
        className={`toggle-option ${mode === "transliterate" ? "active" : ""}`}
        onClick={() => onChange("transliterate")}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 7V4h16v3"/><path d="M9 20h6"/><path d="M12 4v16"/>
        </svg>
        Transliterate
      </button>
    </div>
  );
}
