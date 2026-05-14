class PhoneticMapper:
    """Rule-based phonetic fallback for Indic scripts when neural models are unavailable."""
    def __init__(self):
        # Simple mappings for extreme fallback
        self.basic_map = {
            "te": {
                "namaskaram": "నమస్కారం", "ela": "ఎలా", "unnaru": "ఉన్నారు", 
                "meeru": "మీరు", "bagunnara": "బాగున్నారా", "nenu": "నేను",
                "chala": "చాలా", "bagundi": "బాగుంది"
            },
            "ta": {
                "vanakkam": "வணக்கம்", "epdi": "எப்படி", "irukkinga": "இருக்கீங்க",
                "nalla": "நல்லா", "nan": "நான்"
            },
            "hi": {
                "namaste": "नमस्ते", "kaise": "कैसे", "ho": "हो",
                "kya": "क्या", "haal": "हाल", "hai": "है", "main": "मैं", "theek": "ठीक", "hun": "हूँ"
            }
        }

    def map_word(self, word: str, lang: str) -> str:
        word_lower = word.lower()
        if lang in self.basic_map and word_lower in self.basic_map[lang]:
            return self.basic_map[lang][word_lower]
        return word # Fallback to original
