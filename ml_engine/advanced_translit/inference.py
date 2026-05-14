from .transliteration import TransliterationEngineV3

# Initialize as singleton for the application lifecycle
translit_engine_v3 = TransliterationEngineV3()

# Note: HybridRouter should be instantiated at the API level where the Translation Engine is also available.
