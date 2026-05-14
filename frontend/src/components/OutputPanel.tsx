"use client";

import React, { useState, useRef } from "react";
import type { TranslationResult } from "@/types";
import { generateTTS } from "@/lib/api";
import RomanizedToggle, { RomanizedViewMode } from "./RomanizedToggle";

interface OutputPanelProps {
  result: TranslationResult | null;
  isLoading: boolean;
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 85 ? "var(--success)" :
    pct >= 65 ? "#f59e0b" :
    "var(--error)";
  const label = pct >= 85 ? "High" : pct >= 65 ? "Medium" : "Low";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}` }} />
          <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontWeight: 500 }}>
            {label} Confidence
          </span>
        </div>
        <span style={{ fontSize: "0.8125rem", fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>
          {pct}%
        </span>
      </div>
      <div className="confidence-track">
        <div
          className="confidence-fill"
          style={{
            width: `${pct}%`,
            background: pct >= 85
              ? `linear-gradient(90deg, var(--success), #34d399)`
              : pct >= 65
              ? `linear-gradient(90deg, #f59e0b, #fbbf24)`
              : `linear-gradient(90deg, var(--error), #f87171)`,
          }}
        />
      </div>
    </div>
  );
}

export default function OutputPanel({ result, isLoading }: OutputPanelProps) {
  const [copied, setCopied] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<RomanizedViewMode>('native');
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleCopy = async () => {
    if (!result) return;
    let textToCopy = result.translated_text;
    if (viewMode === 'romanized' && result.romanized_text) {
      textToCopy = result.romanized_text;
    } else if (viewMode === 'both' && result.romanized_text) {
      textToCopy = `${result.translated_text}\n\n${result.romanized_text}`;
    }
    await navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleListen = async () => {
    if (!result || ttsLoading) return;
    setTtsLoading(true);
    try {
      const blob = await generateTTS(result.translated_text, result.target_language);
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.play();
    } catch (e) {
      console.error("TTS failed:", e);
    } finally {
      setTtsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    let textToDl = result.translated_text;
    if (viewMode === 'romanized' && result.romanized_text) {
      textToDl = result.romanized_text;
    } else if (viewMode === 'both' && result.romanized_text) {
      textToDl = `${result.translated_text}\n\n${result.romanized_text}`;
    }
    const blob = new Blob([textToDl], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `translation_${result.target_language}.txt`; a.click();
    URL.revokeObjectURL(url);
  };

  /* ── Loading skeleton ─────────────────────────────────────── */
  if (isLoading) {
    return (
      <div style={{
        height: "100%",
        background: "var(--bg-card)",
        border: "1px solid var(--border-primary)",
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        padding: "22px",
        gap: "14px",
      }}>
        {/* Header skeleton */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div className="skeleton" style={{ width: "140px", height: "18px" }} />
          <div className="skeleton" style={{ width: "80px", height: "24px", borderRadius: "99px" }} />
        </div>

        {/* AI thinking animation */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px" }}>
          <div style={{
            width: "52px", height: "52px",
            borderRadius: "50%",
            background: "var(--accent-muted)",
            display: "flex", alignItems: "center", justifyContent: "center",
            animation: "glow-pulse 2s ease-in-out infinite",
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-bright)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: "spin-slow 3s linear infinite" }}>
              <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
            </svg>
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>AI is translating…</div>
        </div>

        {/* Lines skeleton */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div className="skeleton" style={{ height: "14px", width: "90%" }} />
          <div className="skeleton" style={{ height: "14px", width: "75%" }} />
          <div className="skeleton" style={{ height: "14px", width: "60%" }} />
        </div>
      </div>
    );
  }

  /* ── Empty state ──────────────────────────────────────────── */
  if (!result) {
    return (
      <div style={{
        height: "100%",
        background: "var(--bg-card)",
        border: "1px solid var(--border-primary)",
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "16px",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Glow */}
        <div style={{
          position: "absolute",
          width: "300px", height: "300px",
          borderRadius: "50%",
          background: "var(--gradient-glow)",
          pointerEvents: "none",
        }} />

        <div style={{
          width: "64px", height: "64px",
          background: "var(--accent-muted)",
          borderRadius: "var(--radius-xl)",
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "1px solid var(--border-accent)",
          animation: "float 3s ease-in-out infinite",
        }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-bright)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
          </svg>
        </div>

        <div style={{ textAlign: "center" }}>
          <div style={{ fontWeight: 600, fontSize: "0.9375rem", color: "var(--text-secondary)", marginBottom: "6px" }}>
            Translation will appear here
          </div>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", maxWidth: "200px" }}>
            Enter text and click Translate to get started
          </div>
        </div>

        {/* Language chips decoration */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", justifyContent: "center", maxWidth: "260px" }}>
          {["తెలుగు", "हिन्दी", "বাংলা", "தமிழ்", "ಕನ್ನಡ"].map((s) => (
            <span key={s} style={{
              padding: "3px 10px",
              borderRadius: "99px",
              background: "var(--accent-subtle)",
              border: "1px solid var(--border-accent)",
              fontSize: "0.8125rem",
              color: "var(--accent-bright)",
              opacity: 0.6,
            }}>{s}</span>
          ))}
        </div>
      </div>
    );
  }

  /* ── Result ───────────────────────────────────────────────── */
  return (
    <div
      className="animate-slide-left"
      style={{
        height: "100%",
        background: "var(--bg-card)",
        border: "1px solid var(--border-primary)",
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header - 2 Row Professional Layout */}
      <div style={{
        display: "flex", flexDirection: "column", gap: "14px",
        padding: "16px 20px 14px 20px",
        borderBottom: "1px solid var(--border-subtle)",
        background: "var(--bg-card)",
      }}>
        {/* ROW 1: Title & Actions */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", letterSpacing: "0.01em" }}>
              Translated Output
            </span>
            <span style={{
              padding: "2px 8px",
              borderRadius: "99px",
              background: "var(--accent-muted)",
              border: "1px solid var(--border-accent)",
              fontSize: "0.65rem",
              color: "var(--accent-bright)",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.02em"
            }}>
              {result.mode}
            </span>
          </div>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <button id="copy-btn" className="btn-icon" onClick={handleCopy} title="Copy translation" style={{ color: copied ? "var(--success)" : undefined }}>
              {copied
                ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
              }
            </button>

            <button id="listen-btn" className="btn-icon" onClick={handleListen} title="Listen to translation" style={{ color: ttsLoading ? "var(--accent-bright)" : undefined }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
              </svg>
            </button>

            <button id="download-btn" className="btn-icon" onClick={handleDownload} title="Download as text">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>
              </svg>
            </button>
          </div>
        </div>

        {/* ROW 2: Toggle */}
        {result.romanized_text && (
          <div style={{ width: "100%" }}>
            <RomanizedToggle mode={viewMode} onChange={setViewMode} />
          </div>
        )}
      </div>

      {/* Translation text */}
      <div style={{ flex: 1, padding: "22px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
        {(viewMode === 'native' || viewMode === 'both') && (
          <div>
            {viewMode === 'both' && <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>Native Script</div>}
            <p style={{
              fontSize: "1.125rem",
              lineHeight: "1.85",
              color: "var(--text-primary)",
              fontWeight: 400,
              letterSpacing: "0.005em",
            }}>
              {result.translated_text}
            </p>
          </div>
        )}
        
        {(viewMode === 'romanized' || viewMode === 'both') && result.romanized_text && (
          <div>
            {viewMode === 'both' && <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>Romanized Pronunciation</div>}
            <p style={{
              fontSize: "1.125rem",
              lineHeight: "1.85",
              color: "var(--accent-bright)",
              fontWeight: 400,
              letterSpacing: "0.01em",
            }}>
              {result.romanized_text}
            </p>
          </div>
        )}
      </div>

      {/* Confidence + Source */}
      <div style={{
        padding: "14px 18px",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}>
        <ConfidenceMeter value={result.confidence} />

        {/* Source text preview */}
        <details style={{ cursor: "pointer" }}>
          <summary style={{
            fontSize: "0.72rem",
            color: "var(--text-muted)",
            listStyle: "none",
            display: "flex",
            alignItems: "center",
            gap: "4px",
            userSelect: "none",
          }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m6 9 6 6 6-6"/></svg>
            Show source text
          </summary>
          <div style={{
            marginTop: "8px",
            padding: "10px 12px",
            background: "var(--bg-elevated)",
            borderRadius: "var(--radius-md)",
            fontSize: "0.8125rem",
            color: "var(--text-secondary)",
            lineHeight: "1.6",
            borderLeft: "2px solid var(--border-accent)",
          }}>
            {result.original_text}
          </div>
        </details>
      </div>
    </div>
  );
}
