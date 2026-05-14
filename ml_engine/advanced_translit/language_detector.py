import re

class LanguageDetector:
    def __init__(self):
        # A dictionary of common English words to differentiate from Romanized Indic
        self.english_common = {
            "the", "is", "in", "at", "of", "on", "and", "a", "to", "it", 
            "with", "as", "for", "was", "this", "that", "are", "by", "be",
            "have", "has", "had", "not", "but", "what", "all", "were", "when",
            "we", "there", "can", "an", "your", "which", "their", "said", "if",
            "do", "will", "each", "about", "how", "up", "out", "them", "then",
            "she", "many", "some", "so", "these", "would", "other", "into"
        }

    def detect_script(self, text: str) -> str:
        """Detects if text is primarily Roman or Native Indic script."""
        indic_pattern = re.compile(r'[\u0900-\u0DFF]')
        indic_chars = len(indic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return "roman"
        return "indic" if (indic_chars / total_chars) > 0.3 else "roman"

    def analyze_mixed_content(self, text: str) -> dict:
        """Analyzes string to find mixed English and Romanized Indic."""
        words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
        english_count = sum(1 for w in words if w in self.english_common)
        
        total_words = len(words)
        is_english = english_count > total_words * 0.35 if total_words > 0 else False
        
        return {
            "total_words": total_words,
            "english_words": english_count,
            "is_likely_english_sentence": is_english,
            "is_likely_romanized_indic": not is_english if total_words > 0 else False,
            "confidence": (english_count / total_words) if total_words > 0 else 0.0
        }
