import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# 資料庫
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/memory.db")

# Persona
PERSONA_PATH = Path(os.getenv("PERSONA_PATH", "prompts/persona.md"))