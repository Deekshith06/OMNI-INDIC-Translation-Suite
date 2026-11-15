"use client";

import React from "react";
import type { Language } from "@/types";

interface LanguageSelectorProps {
  id?: string;
  value: string;
  onChange: (lang: string) => void;
  languages?: Language[];
}

const DEFAULT_LANGUAGES: Language[] = [
  { key: "english",   label: "English",   script: "English"  },
  { key: "telugu",    label: "Telugu",    script: "తెలుగు"   },
  { key: "tamil",     label: "Tamil",     script: "தமிழ்"    },
  { key: "kannada",   label: "Kannada",   script: "ಕನ್ನಡ"  },
  { key: "malayalam", label: "Malayalam", script: "മലയാളം"},
  { key: "marathi",   label: "Marathi",   script: "मराठी"  },
  { key: "punjabi",   label: "Punjabi",   script: "ਪੰਜਾਬੀ" },
  { key: "hindi",     label: "Hindi",     script: "हिन्दी"  },
  { key: "bengali",   label: "Bengali",   script: "বাংলা"  },
  { key: "gujarati",  label: "Gujarati",  script: "ગુજરાતી" },
  { key: "odia",      label: "Odia",      script: "ଓଡ଼ିଆ"    },
  { key: "assamese",  label: "Assamese",  script: "অসমীয়া" },
];

export default function LanguageSelector({ id = "language-select", value, onChange, languages = DEFAULT_LANGUAGES }: LanguageSelectorProps) {
  const selected = languages.find(l => l.key === value);

  return (
    <div style={{ position: "relative" }}>
      <select
        id={id}
        className="lang-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {languages.map((lang) => (
          <option key={lang.key} value={lang.key}>
            {lang.label} — {lang.script}
          </option>
        ))}
      </select>
    </div>
  );
}
