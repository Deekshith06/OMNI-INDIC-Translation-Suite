from pydantic import BaseModel
from typing import Optional

class RomanizedOutputResponse(BaseModel):
    original_text: str
    translated_native: str
    romanized_pronunciation: Optional[str] = None
    target_language: str
