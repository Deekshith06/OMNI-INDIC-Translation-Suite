"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import type { InputMode, TranslationMode, TranslationResult, Language, EngineStatus } from "@/types";
import { translateText, translateDocument, fetchLanguages, fetchStatus } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import LanguageSelector from "@/components/LanguageSelector";
import TransliterationToggle from "@/components/TransliterationToggle";
import InputPanel from "@/components/InputPanel";
import OutputPanel from "@/components/OutputPanel";

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE — Omni-Indic v3 AI SaaS UI
   ═══════════════════════════════════════════════════════════════════════ */

export default function Home() {
  // ── State ────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab]             = useState("translate");
  const [sourceLang, setSourceLang]           = useState("english");
  const [targetLang, setTargetLang]           = useState("telugu");
  const [translationMode, setTranslationMode] = useState<TranslationMode>("translate");
  const [inputMode, setInputMode]             = useState<InputMode>("text");
  const [text, setText]                       = useState("");
  const [file, setFile]                       = useState<File | null>(null);
  const [result, setResult]                   = useState<TranslationResult | null>(null);
  const [isLoading, setIsLoading]             = useState(false);
  const [error, setError]                     = useState<string | null>(null);
  const [languages, setLanguages]             = useState<Language[] | undefined>(undefined);
  const [status, setStatus]                   = useState<EngineStatus | null>(null);
  const [swapAnim, setSwapAnim]               = useState(false);

  // ── API bootstrap ────────────────────────────────────────────────────
  useEffect(() => {
    fetchLanguages().then(setLanguages).catch(() => {});
    fetchStatus().then(setStatus).catch(() => {});
  }, []);

  // ── Handlers ─────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      let response: TranslationResult;
      if (inputMode === "text") {
        response = await translateText(text, targetLang, translationMode, sourceLang);
      } else {
        if (!file) throw new Error("No file selected.");
        response = await translateDocument(file, targetLang, translationMode, sourceLang);
      }
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }, [inputMode, text, file, targetLang, sourceLang, translationMode]);

  const handleSwapLanguages = useCallback(() => {
    setSwapAnim(a => !a);
    const prevSource = sourceLang;
    const prevTarget = targetLang;
    setSourceLang(prevTarget);
    setTargetLang(prevSource);

    // If there is an existing translation, swap texts into the input box
    if (result?.translated_text) {
      setText(result.translated_text);
      setResult(null);
    }
  }, [sourceLang, targetLang, result]);

  const handleTabChange = useCallback((tab: string) => {
    setActiveTab(tab);
    if (tab === "documents") setInputMode("pdf");
    else if (tab === "translate") setInputMode("text");
  }, []);

  // ── Keyboard shortcut: Ctrl/Cmd + Enter ────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [handleSubmit]);

  /* ── Engine status dot ──────────────────────────────────────── */
  const engineOnline = status?.translation_engine;

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-app)", overflow: "hidden" }}>

      {/* ── SIDEBAR ──────────────────────────────────────────────── */}
      <Sidebar activeTab={activeTab} onTabChange={handleTabChange} languages={languages} />

      {/* ── MAIN CONTENT ─────────────────────────────────────────── */}
      <main style={{
        flex: 1,
        marginLeft: "220px",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        background: "var(--bg-primary)",
      }}>

        {/* ── TOP BAR ────────────────────────────────────────────── */}
        <header style={{
          height: "60px",
          borderBottom: "1px solid var(--border-subtle)",
          background: "rgba(15,15,23,0.85)",
          backdropFilter: "blur(16px)",
          display: "flex",
          alignItems: "center",
          padding: "0 24px",
          gap: "16px",
          flexShrink: 0,
          position: "sticky",
          top: 0,
          zIndex: 30,
        }}>

          {/* Language swap bar */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1 }}>
            {/* Source language */}
            <LanguageSelector
              id="source-language-select"
              value={sourceLang}
              onChange={setSourceLang}
              languages={languages}
            />

            {/* Swap button */}
            <button
              className={`swap-btn ${swapAnim ? "rotated" : ""}`}
              id="swap-lang-btn"
              title="Swap languages"
              onClick={handleSwapLanguages}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m17 4 4 4-4 4"/><path d="M3 8h18"/><path d="m7 20-4-4 4-4"/><path d="M21 16H3"/>
              </svg>
            </button>

            {/* Target language */}
            <LanguageSelector
              id="target-language-select"
              value={targetLang}
              onChange={setTargetLang}
              languages={languages}
            />
          </div>

          {/* Mode toggle */}
          <TransliterationToggle mode={translationMode} onChange={setTranslationMode} />

          {/* Right: status + shortcut hint */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Keyboard hint */}
            <span style={{
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
              padding: "3px 8px",
              fontFamily: "monospace",
              display: "none", // shown on md+
            }}>
              ⌘↩ Translate
            </span>

            {/* Engine status */}
            <div style={{
              display: "flex", alignItems: "center", gap: "6px",
              padding: "5px 12px",
              borderRadius: "var(--radius-full)",
              background: engineOnline === true
                ? "var(--success-muted)"
                : engineOnline === false
                ? "var(--error-muted)"
                : "rgba(255,255,255,0.04)",
              border: `1px solid ${engineOnline === true ? "rgba(16,185,129,0.2)" : engineOnline === false ? "rgba(239,68,68,0.2)" : "var(--border-subtle)"}`,
            }}>
              <span className={`status-dot ${engineOnline === true ? "online" : engineOnline === false ? "offline" : "loading"}`} />
              <span style={{
                fontSize: "0.72rem",
                fontWeight: 600,
                color: engineOnline === true ? "var(--success)" : engineOnline === false ? "var(--error)" : "var(--text-muted)",
              }}>
                {engineOnline === true ? "Engine Online" : engineOnline === false ? "Demo Mode" : "Connecting…"}
              </span>
            </div>
          </div>
        </header>

        {/* ── Error Banner ─────────────────────────────────────────── */}
        {error && (
          <div
            className="animate-fade-up"
            style={{
              margin: "16px 24px 0",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              background: "var(--error-muted)",
              border: "1px solid rgba(239,68,68,0.25)",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--error)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>
            </svg>
            <span style={{ fontSize: "0.875rem", color: "var(--error)", flex: 1 }}>{error}</span>
            <button className="btn-icon" onClick={() => setError(null)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
              </svg>
            </button>
          </div>
        )}

        {/* ── WORKSPACE ─────────────────────────────────────────────── */}
        <div style={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "16px",
          padding: "20px 24px",
          overflow: "hidden",
          minHeight: 0,
        }}>
          <InputPanel
            text={text}
            onTextChange={setText}
            file={file}
            onFileChange={setFile}
            inputMode={inputMode}
            onInputModeChange={setInputMode}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
          <OutputPanel result={result} isLoading={isLoading} />
        </div>

        {/* ── FOOTER ─────────────────────────────────────────────────── */}
        <footer style={{
          padding: "8px 24px",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
            {languages?.slice(0, 6).map((lang) => (
              <button
                key={lang.key}
                onClick={() => setTargetLang(lang.key)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "2px",
                  padding: "4px 6px",
                  borderRadius: "var(--radius-sm)",
                  transition: "all var(--t-fast)",
                  opacity: targetLang === lang.key ? 1 : 0.45,
                }}
                onMouseEnter={e => (e.currentTarget.style.opacity = "0.9")}
                onMouseLeave={e => (e.currentTarget.style.opacity = targetLang === lang.key ? "1" : "0.45")}
                title={lang.label}
              >
                <span style={{ fontSize: "1rem", lineHeight: 1 }}>{lang.script}</span>
                <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", letterSpacing: "0.04em" }}>
                  {lang.label}
                </span>
              </button>
            ))}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
            Powered by NLLB-200 · {(languages?.length ?? 0)} languages
          </div>
        </footer>
      </main>
    </div>
  );
}
