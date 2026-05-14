"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";

/* ─── Component ────────────────────────────────────────────────────── */

interface AudioPlayerProps {
  audioUrl: string | null;
  onRequestAudio: () => void;
  isGenerating: boolean;
}

export default function AudioPlayer({
  audioUrl,
  onRequestAudio,
  isGenerating,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => {
      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }
    };

    const onLoadedMetadata = () => setDuration(audio.duration);
    const onEnded = () => {
      setIsPlaying(false);
      setProgress(0);
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("ended", onEnded);
    };
  }, [audioUrl]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    if (!audio || !audio.duration) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    audio.currentTime = pos * audio.duration;
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // No audio yet — show "Listen" button
  if (!audioUrl) {
    return (
      <button
        id="listen-btn"
        onClick={onRequestAudio}
        disabled={isGenerating}
        className="btn-secondary"
        style={{ fontSize: "0.8125rem" }}
      >
        {isGenerating ? (
          <>
            <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            Generating...
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
            Listen
          </>
        )}
      </button>
    );
  }

  // Audio loaded — show player
  return (
    <div
      id="audio-player"
      className="flex items-center gap-3 p-3 rounded-lg animate-fade-in-scale"
      style={{ background: "var(--bg-primary)", border: "1px solid var(--border-primary)" }}
    >
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Play / Pause */}
      <button
        onClick={togglePlay}
        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-150"
        style={{ background: "var(--accent)", color: "white" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "var(--accent-hover)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "var(--accent)")}
      >
        {isPlaying ? (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="4" width="4" height="16" rx="1" />
            <rect x="14" y="4" width="4" height="16" rx="1" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="6 3 20 12 6 21 6 3" />
          </svg>
        )}
      </button>

      {/* Progress */}
      <div className="flex-1 flex items-center gap-2">
        <div
          className="flex-1 h-1.5 rounded-full cursor-pointer"
          style={{ background: "var(--bg-tertiary)" }}
          onClick={handleSeek}
        >
          <div
            className="h-full rounded-full"
            style={{
              width: `${progress}%`,
              background: "var(--accent-light)",
              transition: "width 0.1s linear",
            }}
          />
        </div>
        <span className="text-xs tabular-nums" style={{ color: "var(--text-tertiary)", minWidth: "32px" }}>
          {duration ? formatTime(duration) : "0:00"}
        </span>
      </div>

      {/* Download */}
      <a
        href={audioUrl}
        download="translation.mp3"
        className="p-1.5 rounded-md transition-colors duration-150"
        style={{ color: "var(--text-tertiary)" }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
        title="Download audio"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" x2="12" y1="15" y2="3" />
        </svg>
      </a>
    </div>
  );
}
