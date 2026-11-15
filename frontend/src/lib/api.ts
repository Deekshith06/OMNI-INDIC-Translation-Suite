/* ─── Omni-Indic Hybrid Cloud & ZeroGPU API Client ─────────────────── */

import type {
  Language,
  TranslationResult,
  TranslationMode,
  EngineStatus,
} from "@/types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "https://deekshith55717-omni-indic-api.hf.space").replace(/\/$/, "");
const HF_TOKEN = process.env.NEXT_PUBLIC_HF_TOKEN || "";

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {};
  if (HF_TOKEN) {
    headers["Authorization"] = `Bearer ${HF_TOKEN}`;
  }
  return headers;
}

const FALLBACK_LANGUAGES: Language[] = [
  { key: "english", label: "English", script: "Latin" },
  { key: "telugu", label: "Telugu (తెలుగు)", script: "Telugu" },
  { key: "tamil", label: "Tamil (தமிழ்)", script: "Tamil" },
  { key: "kannada", label: "Kannada (ಕನ್ನಡ)", script: "Kannada" },
  { key: "hindi", label: "Hindi (हिन्दी)", script: "Devanagari" },
  { key: "malayalam", label: "Malayalam (മലയാളം)", script: "Malayalam" },
  { key: "marathi", label: "Marathi (मराठी)", script: "Devanagari" },
  { key: "punjabi", label: "Punjabi (ਪੰਜਾਬੀ)", script: "Gurmukhi" },
  { key: "bengali", label: "Bengali (বাংলা)", script: "Bengali" },
  { key: "gujarati", label: "Gujarati (ગુજરાતી)", script: "Gujarati" },
  { key: "odia", label: "Odia (ଓଡ଼ିଆ)", script: "Odia" },
  { key: "assamese", label: "Assamese (অসমীয়া)", script: "Bengali" },
];

/**
 * Execute translation via Hugging Face Space Gradio SSE queue.
 */
async function translateViaHFSpace(
  text: string,
  sourceLang: string,
  targetLang: string,
  mode: TranslationMode
): Promise<TranslationResult> {
  const gradioMode = mode === "transliterate" ? "Transliterate" : "Translate";
  const postRes = await fetch(`${API_BASE}/gradio_api/call/process_text`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ data: [text, sourceLang, targetLang, gradioMode] }),
  });

  if (!postRes.ok) {
    throw new Error(`HF Space Gradio queue request failed: ${postRes.statusText}`);
  }

  const { event_id } = await postRes.json();
  const getRes = await fetch(`${API_BASE}/gradio_api/call/process_text/${event_id}`, {
    headers: getAuthHeaders(),
  });
  const sseText = await getRes.text();
  const dataLine = sseText.split("\n").find((l) => l.startsWith("data: "));
  if (!dataLine) {
    throw new Error("Invalid response stream from Hugging Face Space.");
  }

  const [translated_text, romanized_text, confidence_str] = JSON.parse(
    dataLine.slice(6)
  );

  return {
    original_text: text,
    translated_text,
    target_language: targetLang,
    source_language: sourceLang,
    mode,
    confidence: parseFloat(confidence_str) || 0.88,
    romanized_text: romanized_text || undefined,
  };
}

/**
 * Execute document translation via Hugging Face Space Gradio upload.
 */
async function translateDocumentViaHFSpace(
  file: File,
  sourceLang: string,
  targetLang: string,
  mode: TranslationMode
): Promise<TranslationResult> {
  const gradioMode = mode === "transliterate" ? "Transliterate" : "Translate";
  const formData = new FormData();
  formData.append("files", file);

  const uploadRes = await fetch(`${API_BASE}/gradio_api/upload`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!uploadRes.ok) {
    throw new Error("Failed to upload document to Hugging Face Space.");
  }

  const filePaths = await uploadRes.json();
  const filePath = filePaths[0];

  const postRes = await fetch(`${API_BASE}/gradio_api/call/process_document`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      data: [
        { path: filePath, meta: { _type: "gradio.FileData" } },
        sourceLang,
        targetLang,
        gradioMode,
      ],
    }),
  });

  if (!postRes.ok) {
    throw new Error("Document processing request failed on Hugging Face Space.");
  }

  const { event_id } = await postRes.json();
  const getRes = await fetch(`${API_BASE}/gradio_api/call/process_document/${event_id}`, {
    headers: getAuthHeaders(),
  });
  const sseText = await getRes.text();
  const dataLine = sseText.split("\n").find((l) => l.startsWith("data: "));
  if (!dataLine) {
    throw new Error("Invalid document stream from Hugging Face Space.");
  }

  const [translated_text, romanized_text, extracted_text] = JSON.parse(
    dataLine.slice(6)
  );

  return {
    original_text: extracted_text || file.name,
    translated_text,
    target_language: targetLang,
    source_language: sourceLang,
    mode,
    confidence: 0.95,
    extracted_text,
    romanized_text: romanized_text || undefined,
  };
}

/**
 * Translate text from English/Tinglish to an Indian language or reverse.
 */
export async function translateText(
  text: string,
  targetLang: string,
  mode: TranslationMode = "translate",
  sourceLang: string = "english"
): Promise<TranslationResult> {
  // If pointed to HF Space, call ZeroGPU Gradio endpoint directly
  if (API_BASE.includes(".hf.space")) {
    return translateViaHFSpace(text, sourceLang, targetLang, mode);
  }

  // Otherwise, use REST API endpoint
  try {
    const res = await fetch(`${API_BASE}/api/translate-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_lang: targetLang, source_lang: sourceLang, mode }),
    });

    if (res.ok) {
      return res.json();
    }
  } catch {
    // fallback
  }

  return translateViaHFSpace(text, sourceLang, targetLang, mode);
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
  if (API_BASE.includes(".hf.space")) {
    return translateDocumentViaHFSpace(file, sourceLang, targetLang, mode);
  }

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_lang", targetLang);
    formData.append("source_lang", sourceLang);
    formData.append("mode", mode);

    const res = await fetch(`${API_BASE}/api/translate-doc`, {
      method: "POST",
      body: formData,
    });

    if (res.ok) {
      return res.json();
    }
  } catch {
    // fallback
  }

  return translateDocumentViaHFSpace(file, sourceLang, targetLang, mode);
}

/**
 * Generate TTS audio. Returns a Blob (MP3).
 */
export async function generateTTS(
  text: string,
  lang: string
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/generate-tts`, {
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
  try {
    const res = await fetch(`${API_BASE}/api/languages`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.languages) && data.languages.length > 0) {
        return data.languages;
      }
    }
  } catch {
    // Fallback to static catalog
  }
  return FALLBACK_LANGUAGES;
}

/**
 * Check engine loading status.
 */
export async function fetchStatus(): Promise<EngineStatus> {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (res.ok) {
      return res.json();
    }
  } catch {
    // Fallback
  }
  return {
    translation_engine: true,
    transliteration_engine: true,
    ocr_processor: true,
    pdf_processor: true,
    demo_mode: false,
  };
}
