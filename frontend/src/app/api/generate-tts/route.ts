import { NextRequest, NextResponse } from "next/server";

const GTTS_LANG_CODES: Record<string, string> = {
  telugu: "te",
  tamil: "ta",
  kannada: "kn",
  malayalam: "ml",
  hindi: "hi",
  marathi: "mr",
  punjabi: "pa",
  bengali: "bn",
  gujarati: "gu",
  odia: "or",
  assamese: "as",
  english: "en",
};

export async function POST(req: NextRequest) {
  try {
    const { text, lang } = await req.json();

    if (!text || typeof text !== "string" || !text.trim()) {
      return NextResponse.json({ detail: "Text cannot be empty." }, { status: 400 });
    }

    const langCode = GTTS_LANG_CODES[lang?.toLowerCase()] || "hi";
    const googleTTSUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(
      text.slice(0, 200)
    )}&tl=${langCode}&client=tw-ob`;

    const audioRes = await fetch(googleTTSUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      },
    });

    if (!audioRes.ok) {
      return NextResponse.json({ detail: "Failed to generate TTS audio." }, { status: audioRes.status });
    }

    const audioBuffer = await audioRes.arrayBuffer();

    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=86400, s-maxage=86400",
      },
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "TTS generation failed." }, { status: 500 });
  }
}
