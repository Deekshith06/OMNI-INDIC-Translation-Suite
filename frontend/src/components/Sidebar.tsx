"use client";

import React from "react";
import type { Language } from "@/types";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  languages?: Language[];
}

const NAV = [
  {
    id: "translate",
    label: "Translate",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
      </svg>
    ),
  },
  {
    id: "documents",
    label: "Documents",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/>
      </svg>
    ),
  },
  {
    id: "history",
    label: "History",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>
      </svg>
    ),
  },
];

const QUICK_LANGS = ["Hindi", "Telugu", "Tamil", "Bengali"];

export default function Sidebar({ activeTab, onTabChange, languages }: SidebarProps) {
  return (
    <aside
      style={{
        width: "220px",
        height: "100vh",
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        position: "fixed",
        top: 0,
        left: 0,
        zIndex: 40,
      }}
    >
      {/* Logo */}
      <div style={{
        padding: "20px 18px 16px",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "34px", height: "34px",
            background: "var(--gradient-primary)",
            borderRadius: "10px",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 4px 12px var(--accent-glow)",
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
            </svg>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
              Omni-Indic
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              AI Translation
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: "12px 10px", flex: 1, overflowY: "auto" }}>
        <div style={{ marginBottom: "6px" }}>
          {NAV.map((item) => (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              onClick={() => onTabChange(item.id)}
              className={`nav-item ${activeTab === item.id ? "active" : ""}`}
              style={{ width: "100%", textAlign: "left" }}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>

        {/* Quick Languages */}
        <div style={{ marginTop: "24px" }}>
          <div style={{
            fontSize: "0.65rem",
            fontWeight: 600,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
            padding: "0 4px",
            marginBottom: "8px",
          }}>
            Quick Access
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {(languages ?? []).slice(0, 6).map((lang) => (
              <div
                key={lang.key}
                className="nav-item"
                style={{ padding: "7px 12px", fontSize: "0.8125rem" }}
              >
                <span style={{ fontSize: "0.95rem", lineHeight: 1 }}>{lang.script}</span>
                <span style={{ color: "var(--text-secondary)" }}>{lang.label}</span>
              </div>
            ))}
          </div>
        </div>
      </nav>

      {/* Bottom */}
      <div style={{
        padding: "12px 10px",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
      }}>
        {/* Engine Status */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px 12px",
          borderRadius: "var(--radius-md)",
          background: "var(--success-muted)",
          border: "1px solid rgba(16,185,129,0.15)",
        }}>
          <span className="status-dot online" />
          <span style={{ fontSize: "0.75rem", color: "var(--success)", fontWeight: 500 }}>
            NLLB-200 Ready
          </span>
        </div>

        {/* Version */}
        <div style={{ textAlign: "center", padding: "6px", color: "var(--text-muted)", fontSize: "0.65rem" }}>
          v2.1.0 · 11 Languages
        </div>
      </div>
    </aside>
  );
}
