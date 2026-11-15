import { NextResponse } from "next/server";

const LANGUAGES = [
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

export async function GET() {
  return NextResponse.json({ languages: LANGUAGES });
}
