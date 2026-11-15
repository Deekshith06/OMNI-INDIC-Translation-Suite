import { NextRequest, NextResponse } from "next/server";

const HF_SPACE_URL = (
  process.env.HF_SPACE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://deekshith55717-omni-indic-api.hf.space"
).replace(/\/$/, "");

const HF_TOKEN = process.env.HF_TOKEN || process.env.NEXT_PUBLIC_HF_TOKEN || "";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    const target_lang = (formData.get("target_lang") as string) || "hindi";
    const source_lang = (formData.get("source_lang") as string) || "english";
    const mode = (formData.get("mode") as string) || "translate";

    if (!file) {
      return NextResponse.json({ detail: "No file provided." }, { status: 400 });
    }

    const authHeaders: Record<string, string> = {};
    if (HF_TOKEN) {
      authHeaders["Authorization"] = `Bearer ${HF_TOKEN}`;
    }

    // Upload to HF Space
    const uploadForm = new FormData();
    uploadForm.append("files", file);

    const uploadRes = await fetch(`${HF_SPACE_URL}/gradio_api/upload`, {
      method: "POST",
      headers: authHeaders,
      body: uploadForm,
    });

    if (!uploadRes.ok) {
      return NextResponse.json(
        { detail: "Failed to upload document to Hugging Face Space." },
        { status: uploadRes.status }
      );
    }

    const filePaths = await uploadRes.json();
    const filePath = filePaths[0];

    const gradioMode = mode === "transliterate" ? "Transliterate" : "Translate";

    const postRes = await fetch(`${HF_SPACE_URL}/gradio_api/call/process_document`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify({
        data: [
          { path: filePath, meta: { _type: "gradio.FileData" } },
          source_lang.toLowerCase(),
          target_lang.toLowerCase(),
          gradioMode,
        ],
      }),
    });

    if (!postRes.ok) {
      return NextResponse.json(
        { detail: "Document processing failed on Hugging Face Space." },
        { status: postRes.status }
      );
    }

    const { event_id } = await postRes.json();
    const getRes = await fetch(`${HF_SPACE_URL}/gradio_api/call/process_document/${event_id}`, {
      headers: authHeaders,
    });

    const sseText = await getRes.text();
    const dataLine = sseText.split("\n").find((l) => l.startsWith("data: "));
    if (!dataLine) {
      return NextResponse.json(
        { detail: "Invalid response stream from Hugging Face Space." },
        { status: 502 }
      );
    }

    const [translated_text, romanized_text, extracted_text] = JSON.parse(
      dataLine.slice(6)
    );

    return NextResponse.json({
      original_text: extracted_text || file.name,
      translated_text: translated_text || "",
      target_language: target_lang,
      source_language: source_lang,
      mode,
      confidence: 0.95,
      extracted_text: extracted_text || undefined,
      romanized_text: romanized_text || undefined,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Document translation failed." }, { status: 500 });
  }
}
