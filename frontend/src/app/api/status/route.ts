import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    translation_engine: true,
    transliteration_engine: true,
    ocr_processor: true,
    pdf_processor: true,
    demo_mode: false,
    service: "Omni-Indic Translation Suite",
    status: "running",
    version: "2.1.0",
  });
}
