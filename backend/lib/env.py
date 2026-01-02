import os

import dotenv

dotenv.load_dotenv()

DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///data/db.sqlite")

OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://ai.hackclub.com/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("no api key in env")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "google/gemini-3-flash-preview")
QUESTION_MODEL = os.getenv("QUESTION_MODEL", DEFAULT_MODEL)
REVIEW_MODEL = os.getenv("REVIEW_MODEL", DEFAULT_MODEL)
ARTIST_MODEL = os.getenv("ARTIST_MODEL", DEFAULT_MODEL) # Part 1 Image generator
