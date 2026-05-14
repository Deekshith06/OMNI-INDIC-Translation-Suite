/* ─── Omni-Indic Type Definitions ──────────────────────────────────── */

export interface Language {
  key: string;
  label: string;
  script: string;
}

export interface TranslationResult {
  original_text: string;
  translated_text: string;
  romanized_text?: string;
  target_language: string;
  mode: TranslationMode;
  confidence: number;
  extracted_text?: string;
}

export type InputMode = "text" | "voice" | "image" | "pdf";
export type TranslationMode = "translate" | "transliterate";

export interface EngineStatus {
  translation_engine: boolean;
  transliteration_engine: boolean;
  ocr_processor: boolean;
  pdf_processor: boolean;
}

export interface TTSRequest {
  text: string;
  lang: string;
}

export interface TextTranslateRequest {
  text: string;
  target_lang: string;
  mode: TranslationMode;
}
