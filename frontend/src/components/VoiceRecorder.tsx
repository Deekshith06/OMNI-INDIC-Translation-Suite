"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";

/* ─── Component ────────────────────────────────────────────────────── */

interface VoiceRecorderProps {
  onTranscript: (text: string) => void;
}

export default function VoiceRecorder({ onTranscript }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [transcript, setTranscript] = useState("");
  const [interimText, setInterimText] = useState("");
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      let final = "";
      let interim = "";
      for (let i = 0; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript + " ";
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setTranscript(final.trim());
      setInterimText(interim);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      if (event.error !== "no-speech") {
        setIsRecording(false);
      }
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch {}
      }
    };
  }, []);

  const toggleRecording = useCallback(() => {
    if (!recognitionRef.current) return;

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      setTranscript("");
      setInterimText("");
      recognitionRef.current.start();
      setIsRecording(true);
    }
  }, [isRecording]);

  const handleUseTranscript = useCallback(() => {
    const fullText = (transcript + " " + interimText).trim();
    if (fullText) {
      onTranscript(fullText);
    }
  }, [transcript, interimText, onTranscript]);

  const fullDisplay = (transcript + " " + interimText).trim();

  if (!isSupported) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
          style={{ background: "var(--bg-tertiary)" }}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--text-tertiary)" }}>
            <line x1="1" x2="23" y1="1" y2="23" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
            <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .26-.02.51-.05.76" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        </div>
        <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
          Voice input not supported
        </p>
        <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
          Please use Chrome or Edge for speech recognition
        </p>
      </div>
    );
  }

  return (
    <div id="voice-recorder" className="flex flex-col items-center justify-center h-full gap-5 p-6">
      {/* Microphone Button */}
      <button
        onClick={toggleRecording}
        className="relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200"
        style={{
          background: isRecording ? "var(--error)" : "var(--accent)",
          color: "white",
          boxShadow: isRecording
            ? "0 0 0 6px rgba(220, 38, 38, 0.15), 0 4px 20px rgba(220, 38, 38, 0.3)"
            : "0 4px 20px rgba(79, 70, 229, 0.25)",
        }}
      >
        {isRecording && (
          <span
            className="absolute inset-0 rounded-full"
            style={{
              border: "3px solid rgba(255,255,255,0.3)",
              animation: "pulse-record 1.5s ease-in-out infinite",
            }}
          />
        )}
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" x2="12" y1="19" y2="22" />
        </svg>
      </button>

      <p className="text-sm font-medium" style={{ color: isRecording ? "var(--error)" : "var(--text-secondary)" }}>
        {isRecording ? "Listening... Tap to stop" : "Tap to start speaking"}
      </p>

      {/* Live Transcript */}
      {fullDisplay && (
        <div className="w-full animate-fade-in">
          <div
            className="p-4 rounded-xl text-sm leading-relaxed"
            style={{
              background: "var(--bg-tertiary)",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
              minHeight: "80px",
            }}
          >
            {transcript && <span>{transcript} </span>}
            {interimText && (
              <span style={{ color: "var(--text-tertiary)", fontStyle: "italic" }}>
                {interimText}
              </span>
            )}
          </div>
          <div className="flex justify-end mt-3 gap-2">
            <button
              onClick={() => { setTranscript(""); setInterimText(""); }}
              className="btn-secondary text-xs"
            >
              Clear
            </button>
            <button
              onClick={handleUseTranscript}
              className="btn-primary text-xs"
              style={{ padding: "6px 16px" }}
            >
              Use this text →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
