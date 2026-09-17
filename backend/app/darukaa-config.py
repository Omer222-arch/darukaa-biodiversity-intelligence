import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
CORS_ORIGINS = [
    x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",")
    if x.strip()
]
TOP_K = int(os.getenv("TOP_K", "5"))
