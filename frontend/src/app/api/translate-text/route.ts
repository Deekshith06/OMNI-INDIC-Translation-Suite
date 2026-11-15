import { NextRequest, NextResponse } from "next/server";

const HF_SPACE_URL = (
  process.env.HF_SPACE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://deekshith55717-omni-indic-api.hf.space"
).replace(/\/$/, "");

// Private token stored ONLY on server (Vercel environment variable)
const HF_TOKEN = process.env.HF_TOKEN || process.env.NEXT_PUBLIC_HF_TOKEN || "";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { text, target_lang, source_lang = "english", mode = "translate" } = body;

    if (!text || typeof text !== "string" || !text.trim()) {
      return NextResponse.json({ detail: "Text cannot be empty." }, { status: 400 });
    }

    const gradioMode = mode === "transliterate" ? "Transliterate" : "Translate";

    // Call private Hugging Face Space ZeroGPU queue
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (HF_TOKEN) {
      headers["Authorization"] = `Bearer ${HF_TOKEN}`;
    }

    const postRes = await fetch(`${HF_SPACE_URL}/gradio_api/call/process_text`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        data: [text.trim(), source_lang.toLowerCase(), target_lang.toLowerCase(), gradioMode],
      }),
    });

    if (!postRes.ok) {
      const errText = await postRes.text().catch(() => "");
      return NextResponse.json(
        { detail: `Hugging Face Space error (${postRes.status}): ${errText || postRes.statusText}` },
        { status: postRes.status }
      );
    }

    const { event_id } = await postRes.json();
    const getHeaders: Record<string, string> = {};
    if (HF_TOKEN) {
      getHeaders["Authorization"] = `Bearer ${HF_TOKEN}`;
    }

    const getRes = await fetch(`${HF_SPACE_URL}/gradio_api/call/process_text/${event_id}`, {
      headers: getHeaders,
    });

    const sseText = await getRes.text();
    const dataLine = sseText.split("\n").find((l) => l.startsWith("data: "));
    if (!dataLine) {
      return NextResponse.json(
        { detail: "No response data returned from Hugging Face Space." },
        { status: 502 }
      );
    }

    const data = JSON.parse(dataLine.slice(6));
    if (data?.error) {
      return NextResponse.json({ detail: data.error }, { status: 429 });
    }

    const [translated_text, romanized_text, confidence_str] = data;

    return NextResponse.json({
      original_text: text,
      translated_text: translated_text || "",
      target_language: target_lang,
      source_language: source_lang,
      mode,
      confidence: parseFloat(confidence_str) || 0.85,
      romanized_text: romanized_text || undefined,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Translation failed." }, { status: 500 });
  }
}
