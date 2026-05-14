"use client";

import React from "react";

interface InputPanelProps {
  text: string;
  onTextChange: (v: string) => void;
  file: File | null;
  onFileChange: (f: File | null) => void;
  inputMode: string;
  onInputModeChange: (m: any) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const MODES = [
  { id: "text", label: "Text", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 6.1H3"/><path d="M21 12.1H3"/><path d="M15.1 18H3"/></svg> },
  { id: "voice", label: "Voice", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> },
  { id: "image", label: "Image", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg> },
  { id: "pdf", label: "PDF", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg> },
];

const MAX_CHARS = 5000;

export default function InputPanel({
  text, onTextChange, file, onFileChange,
  inputMode, onInputModeChange, onSubmit, isLoading,
}: InputPanelProps) {
  const pct = (text.length / MAX_CHARS) * 100;
  const overLimit = text.length > MAX_CHARS;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      background: "var(--bg-card)",
      border: "1px solid var(--border-primary)",
      borderRadius: "var(--radius-xl)",
      overflow: "hidden",
      position: "relative",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 18px",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        {/* Mode tabs */}
        <div style={{ display: "flex", gap: "2px", background: "var(--bg-input)", padding: "3px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
          {MODES.map((m) => (
            <button
              key={m.id}
              id={`mode-${m.id}`}
              onClick={() => onInputModeChange(m.id)}
              className={`mode-tab ${inputMode === m.id ? "active" : ""}`}
            >
              {m.icon}
              {m.label}
            </button>
          ))}
        </div>

        {/* Clear */}
        {text && (
          <button
            className="btn-icon"
            onClick={() => { onTextChange(""); onFileChange(null); }}
            title="Clear input"
            style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        )}
      </div>

      {/* Text input area */}
      {inputMode === "text" && (
        <div style={{ flex: 1, padding: "20px 22px", display: "flex", flexDirection: "column" }}>
          <textarea
            id="translation-input"
            className="ai-textarea"
            value={text}
            onChange={(e) => onTextChange(e.target.value)}
            placeholder="Type or paste English / Tinglish text to translate…"
            style={{ flex: 1, fontSize: "1.0625rem", lineHeight: "1.75" }}
            spellCheck={false}
          />
        </div>
      )}

      {/* File upload area */}
      {(inputMode === "image" || inputMode === "pdf") && (
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
          <label
            htmlFor="file-upload"
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "14px",
              border: "2px dashed var(--border-primary)",
              borderRadius: "var(--radius-lg)",
              cursor: "pointer",
              transition: "all var(--t-base)",
              background: file ? "var(--accent-subtle)" : "transparent",
              borderColor: file ? "var(--accent)" : undefined,
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f) onFileChange(f);
            }}
          >
            <div style={{
              width: "52px", height: "52px",
              background: "var(--accent-muted)",
              borderRadius: "var(--radius-lg)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {inputMode === "pdf"
                ? <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent-bright)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                : <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent-bright)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
              }
            </div>
            {file
              ? <div style={{ textAlign: "center" }}>
                  <div style={{ fontWeight: 600, color: "var(--accent-bright)", fontSize: "0.875rem" }}>{file.name}</div>
                  <div style={{ color: "var(--text-tertiary)", fontSize: "0.75rem", marginTop: "4px" }}>{(file.size / 1024).toFixed(0)} KB</div>
                </div>
              : <div style={{ textAlign: "center" }}>
                  <div style={{ fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                    Drop {inputMode === "pdf" ? "PDF" : "image"} here
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: "4px" }}>
                    or click to browse · max 10 MB
                  </div>
                </div>
            }
            <input
              id="file-upload"
              type="file"
              accept={inputMode === "pdf" ? ".pdf" : "image/*"}
              style={{ display: "none" }}
              onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
      )}

      {/* Voice placeholder */}
      {inputMode === "voice" && (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "16px" }}>
          <div style={{
            width: "72px", height: "72px",
            background: "var(--accent-muted)",
            borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center",
            border: "2px solid var(--border-accent)",
          }}>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--accent-bright)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" x2="12" y1="19" y2="22"/>
            </svg>
          </div>
          <span style={{ color: "var(--text-tertiary)", fontSize: "0.875rem" }}>Voice input coming soon</span>
        </div>
      )}

      {/* Footer bar */}
      <div style={{
        padding: "12px 18px",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
      }}>
        {/* Char count */}
        {inputMode === "text" && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1 }}>
            <div style={{ flex: 1, height: "2px", background: "var(--border-subtle)", borderRadius: "99px", overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${Math.min(pct, 100)}%`,
                background: overLimit ? "var(--error)" : pct > 80 ? "var(--warning)" : "var(--gradient-primary)",
                borderRadius: "99px",
                transition: "width 0.2s ease",
              }} />
            </div>
            <span style={{ fontSize: "0.72rem", color: overLimit ? "var(--error)" : "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
              {text.length.toLocaleString()} / {MAX_CHARS.toLocaleString()}
            </span>
          </div>
        )}
        {inputMode !== "text" && <div style={{ flex: 1 }} />}

        {/* Translate button */}
        <button
          id="translate-button"
          className="btn-primary"
          onClick={onSubmit}
          disabled={isLoading || overLimit || (!text.trim() && !file)}
          style={{ minWidth: "130px" }}
        >
          {isLoading ? (
            <>
              <div style={{ display: "flex", gap: "3px" }}>
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
              Translating
            </>
          ) : (
            <>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
              </svg>
              Translate
            </>
          )}
        </button>
      </div>
    </div>
  );
}
