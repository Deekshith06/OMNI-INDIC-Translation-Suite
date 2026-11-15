import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
};

export const metadata: Metadata = {
  title: "Omni-Indic | AI Translation Suite",
  description:
    "Premium AI-powered translation and transliteration from English/Tinglish to 11 Indian languages — powered by NLLB-200.",
  keywords: ["translation", "Indian languages", "AI", "Telugu", "Hindi", "Tamil", "Bengali", "Kannada", "NLLB"],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="h-full antialiased">
        {children}
      </body>
    </html>
  );
}
