import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() 

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data")).resolve()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "azure")
AZURE_TTS_KEY = os.environ.get("AZURE_TTS_KEY", "")
AZURE_TTS_ENDPOINT = os.environ.get("AZURE_TTS_ENDPOINT", "")
ADOBE_EMBED_API_KEY = os.environ.get("ADOBE_EMBED_API_KEY", "")

MAX_PDFS_PER_ZIP = int(os.environ.get("MAX_PDFS_PER_ZIP", "200"))

for sub in ["docs", "meta", "vecs", "index", "audio", "tmp", "logs"]:
    (DATA_DIR / sub).mkdir(parents=True, exist_ok=True)
