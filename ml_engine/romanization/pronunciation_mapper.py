import unicodedata

class PronunciationMapper:
    """Converts academic ISO transliteration into human-readable English pronunciation."""
    def __init__(self):
        # Phonetic approximations for natural English reading
        self.replacements = {
            'ī': 'ee',
            'ū': 'oo',
            'ś': 'sh',
            'ṣ': 'sh',
            'c': 'ch', 
            'ch': 'chh',
            'ñ': 'ny',
            'ā': 'aa',
            'ṛ': 'ru'
        }

    def map_to_human(self, iso_text: str) -> str:
        text = iso_text
        for k, v in self.replacements.items():
            text = text.replace(k, v)
            text = text.replace(k.upper(), v.capitalize())
            
        # Strip remaining diacritics
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text
