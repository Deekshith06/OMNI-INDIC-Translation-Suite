/* ─── Omni-Indic Clean Client ────────────────────────────────────────── */

import type {
  Language,
  TranslationResult,
  TranslationMode,
  EngineStatus,
} from "@/types";

/**
 * Translate text from English/Tinglish to an Indian language or reverse.
 */
export async function translateText(
  text: string,
  targetLang: string,
  mode: TranslationMode = "translate",
  sourceLang: string = "english"
): Promise<TranslationResult> {
  const res = await fetch("/api/translate-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang: targetLang, source_lang: sourceLang, mode }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Translation failed");
  }

  return res.json();
}

/**
 * Translate a document (image for OCR or PDF).
 */
export async function translateDocument(
  file: File,
  targetLang: string,
  mode: TranslationMode = "translate",
  sourceLang: string = "english"
): Promise<TranslationResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_lang", targetLang);
  formData.append("source_lang", sourceLang);
  formData.append("mode", mode);

  const res = await fetch("/api/translate-doc", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Document translation failed");
  }

  return res.json();
}

/**
 * Generate TTS audio. Returns a Blob (MP3).
 */
export async function generateTTS(
  text: string,
  lang: string
): Promise<Blob> {
  const res = await fetch("/api/generate-tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, lang }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "TTS generation failed");
  }

  return res.blob();
}

/**
 * Fetch the list of supported languages.
 */
export async function fetchLanguages(): Promise<Language[]> {
  const res = await fetch("/api/languages");
  if (!res.ok) throw new Error("Failed to fetch languages");
  const data = await res.json();
  return data.languages;
}

/**
 * Check engine loading status.
 */
export async function fetchStatus(): Promise<EngineStatus> {
  const res = await fetch("/api/status");
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}
