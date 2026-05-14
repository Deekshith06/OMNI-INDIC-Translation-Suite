from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from .inference import translit_engine_v3
from .suggestion_engine import SuggestionEngine

router = APIRouter(prefix="/v3/translit", tags=["Transliteration V3"])
suggestion_engine = SuggestionEngine(translit_engine_v3)

class TranslitRequest(BaseModel):
    text: str
    target_lang: str

@router.on_event("startup")
async def startup_event():
    translit_engine_v3.load()

@router.post("/process")
async def transliterate_text(req: TranslitRequest):
    try:
        # In actual usage, target_lang should be mapped to the xlit shortcode (e.g. 'te' for 'telugu')
        res = translit_engine_v3.transliterate_sentence(req.text, req.target_lang)
        return {"original": req.text, "result": res, "target_lang": req.target_lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest")
async def suggest_word(word: str = Query(...), lang: str = Query(...)):
    try:
        res = suggestion_engine.get_live_suggestions(word, lang, limit=5)
        return {"word": word, "suggestions": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
