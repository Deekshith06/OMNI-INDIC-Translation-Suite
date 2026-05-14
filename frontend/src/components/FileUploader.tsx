"use client";

import React, { useCallback, useState } from "react";

/* ─── Component ────────────────────────────────────────────────────── */

interface FileUploaderProps {
  accept: string;
  label: string;
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export default function FileUploader({
  accept,
  label,
  onFileSelect,
  selectedFile,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] || null;
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div id="file-uploader">
      {selectedFile ? (
        /* ─── File Preview ──────────────────────────────────────── */
        <div
          className="flex items-center justify-between p-4 rounded-xl animate-fade-in-scale"
          style={{
            background: "var(--bg-primary)",
            border: "1px solid var(--border-accent)",
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: "var(--accent-muted)", color: "var(--accent-light)" }}
            >
              {selectedFile.type.includes("pdf") ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
                  <path d="M14 2v4a2 2 0 0 0 2 2h4" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                  <circle cx="9" cy="9" r="2" />
                  <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
                </svg>
              )}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {selectedFile.name}
              </p>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                {formatSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <button
            onClick={() => onFileSelect(null)}
            className="flex-shrink-0 p-1.5 rounded-md transition-colors duration-150"
            style={{ color: "var(--text-tertiary)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--error)";
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-tertiary)";
              e.currentTarget.style.background = "transparent";
            }}
            title="Remove file"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6 6 18" /><path d="m6 6 12 12" />
            </svg>
          </button>
        </div>
      ) : (
        /* ─── Drop Zone ─────────────────────────────────────────── */
        <label
          className="block cursor-pointer rounded-xl p-8 text-center transition-all duration-200"
          style={{
            border: `2px dashed ${isDragging ? "var(--accent)" : "var(--border-primary)"}`,
            background: isDragging ? "var(--accent-muted)" : "var(--bg-primary)",
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept={accept}
            onChange={handleChange}
            className="hidden"
          />
          <div
            className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center"
            style={{
              background: isDragging ? "var(--accent)" : "var(--bg-tertiary)",
              color: isDragging ? "white" : "var(--text-secondary)",
              transition: "all var(--transition-fast)",
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" x2="12" y1="3" y2="15" />
            </svg>
          </div>
          <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
            {label}
          </p>
          <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
            Drag & drop or click to browse · Max 10 MB
          </p>
        </label>
      )}
    </div>
  );
}
