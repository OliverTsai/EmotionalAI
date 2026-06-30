# EmotionalAI

EmotionalAI 是一個基於 Python 的情感型 Telegram 聊天機器人專案。  
它透過 Telegram Bot 作為使用者介面，並使用本機端 Ollama Large Language Model 作為 AI 回覆核心。

本專案包含：

- Telegram Bot 聊天介面
- 本機 Ollama LLM 推論
- SQLite 長期記憶資料庫
- Persona 系統提示詞
- 使用者對話歷史紀錄
- 可延伸的情緒型 AI 架構

---

## 目錄

```text
EmotionalAI/
├── ai/
│   ├── memory.py
│   ├── ollama_client.py
│   └── __pycache__/
├── bot/
│   ├── telegram_bot.py
│   ├── __init__.py
│   └── __pycache__/
├── database/
│   └── memory.db
├── logs/
├── memory/
├── prompts/
│   └── persona.md
├── settings/
├── .venv/
├── config.py
├── test.py
├── pyvenv.cfg
└── README.md
```

---

# 1. 專案需求

## 1.1 系統需求

建議使用以下環境：

- Windows 10 / Windows 11
- macOS
- Linux
- Python 3.10 或以上版本
- Ollama
- Telegram Bot Token

> 專案目前可能參考 Python 3.14 環境，但若本機尚未安裝 Python 3.14，也可以先使用 Python 3.10、3.11、3.12 或 3.13 測試。

---

## 1.2 主要套件

本專案使用：

- `python-telegram-bot`
- `requests`
- `sqlite3`
- `python-dotenv`，建議加入
- `ollama` 本機服務

---

# 2. 從零開始安裝

---

## 2.1 安裝 Python

請先安裝 Python3.12.10版本。

### Windows

前往 Python 官方網站下載：

```text
https://www.python.org/downloads/
```

安裝時請務必勾選：

```text
Add Python to PATH
```

安裝完成後，在終端機確認版本：

```bash
python --version
```

或：

```bash
py --version
```

---

### macOS

可以使用 Homebrew 安裝：

```bash
brew install python
```

確認版本：

```bash
python3 --version
```

---

### Linux Ubuntu / Debian

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

確認版本：

```bash
python3 --version
```

---

# 3. 安裝 Ollama

Ollama 是本專案用來在本機執行大型語言模型的工具。

---

## 3.1 Windows / macOS 安裝 Ollama

請到 Ollama 官方網站下載：

```text
https://ollama.com/
```

下載並安裝完成後，開啟終端機確認：

```bash
ollama --version
```

如果有顯示版本，即代表安裝成功。

---

## 3.2 Linux 安裝 Ollama

Linux 可以使用官方安裝指令：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

確認版本：

```bash
ollama --version
```

---

# 4. 下載 AI 模型

安裝 Ollama 後，需要下載一個本機模型。

推薦模型如下：

## 4.1 較推薦：Llama 3.1 8B

```bash
ollama pull llama3.1
```

啟動測試：

```bash
ollama run llama3.1
```

---

## 4.2 較輕量：Llama 3.2 3B

如果電腦效能較普通，可以使用比較小的模型：

```bash
ollama pull llama3.2
```

啟動測試：

```bash
ollama run llama3.2
```

---

## 4.3 中文能力較佳的模型，可選

如果你希望中文對話效果較好，也可以嘗試：

```bash
ollama pull qwen2.5
```

或：

```bash
ollama pull qwen2.5:7b
```

啟動測試：

```bash
ollama run qwen2.5
```

---

## 4.4 查看已安裝模型

```bash
ollama list
```

範例輸出：

```text
NAME             ID              SIZE      MODIFIED
llama3.1         xxxxxxxx        4.7 GB    ...
qwen2.5          xxxxxxxx        4.7 GB    ...
```

---

# 5. 啟動 Ollama 服務

通常 Ollama 安裝後會自動在背景執行。

預設 API 位址為：

```text
http://localhost:11434
```

你可以用瀏覽器開啟：

```text
http://localhost:11434
```

如果看到：

```text
Ollama is running
```

代表 Ollama 服務正常。

---

# 6. 建立 Telegram Bot

---

## 6.1 向 BotFather 建立機器人

1. 打開 Telegram
2. 搜尋：

```text
@BotFather
```

3. 輸入：

```text
/newbot
```

4. 依照指示輸入：
   - Bot 顯示名稱
   - Bot 使用者名稱，必須以 `bot` 結尾，例如：`my_emotional_ai_bot`

5. 建立完成後，BotFather 會給你一組 Token，例如：

```text
1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

請保存這組 Token，稍後會用到。

---

# 7. 下載或放置專案

如果是從 GitHub 下載：

```bash
git clone https://github.com/your-username/EmotionalAI.git
```

進入專案資料夾：

```bash
cd EmotionalAI
```

如果你是使用壓縮檔，請解壓縮後進入專案根目錄。

---

# 8. 建立 Python 虛擬環境

建議使用虛擬環境，避免套件版本互相影響。

---

## 8.1 Windows

```bash
python -m venv .venv
```

啟動虛擬環境：

```bash
.venv\Scripts\activate
```

如果使用 PowerShell 出現權限問題，可先執行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然後再執行：

```powershell
.venv\Scripts\activate
```

---

## 8.2 macOS / Linux

```bash
python3 -m venv .venv
```

啟動虛擬環境：

```bash
source .venv/bin/activate
```

---

## 8.3 確認虛擬環境已啟動

啟動成功後，終端機前面通常會出現：

```text
(.venv)
```

例如：

```text
(.venv) EmotionalAI %
```

---

# 9. 安裝 Python 套件

建議先升級 pip：

```bash
python -m pip install --upgrade pip
```

安裝必要套件：

```bash
pip install python-telegram-bot==20.8 requests python-dotenv
```

如果你之後建立了 `requirements.txt`，則可以改用：

```bash
pip install -r requirements.txt
```

安裝模型的指令：
```bash
ollama pull llama3.1
``````

---

## 9.1 建議的 requirements.txt

你可以在專案根目錄建立 `requirements.txt`：

```txt
python-telegram-bot==20.8
requests
python-dotenv
```

之後其他人只需要執行：

```bash
pip install -r requirements.txt
```

即可安裝依賴套件。

---

# 10. 設定環境變數

建議使用 `.env` 檔案保存敏感資訊，例如 Telegram Token。

在專案根目錄建立 `.env`：

```env
TELEGRAM_BOT_TOKEN=你的_Telegram_Bot_Token
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
DATABASE_PATH=database/memory.db
PERSONA_PATH=prompts/persona.md
```

範例：

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
DATABASE_PATH=database/memory.db
PERSONA_PATH=prompts/persona.md
```

> 注意：請不要把 `.env` 上傳到 GitHub。

---

# 11. 設定 config.py

如果專案目前使用 `config.py` 管理設定，可以設計成讀取 `.env`。

範例：

```python
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

DATABASE_PATH = os.getenv("DATABASE_PATH", "database/memory.db")
PERSONA_PATH = os.getenv("PERSONA_PATH", "prompts/persona.md")

LOG_DIR = "logs"
```

---

# 12. 建立必要資料夾

如果資料夾不存在，請建立：

```bash
mkdir database
mkdir logs
mkdir memory
mkdir prompts
mkdir settings
```

Windows PowerShell 可以使用：

```powershell
mkdir database, logs, memory, prompts, settings
```

---

# 13. 建立 Persona 提示詞

在 `prompts/persona.md` 建立角色設定。

範例：

```markdown
# Persona

你是一個溫柔、具有同理心的情感型 AI 助理。

你的對話風格：

- 溫柔
- 耐心
- 不批判
- 願意傾聽
- 能夠陪伴使用者整理情緒
- 不假裝自己是人類
- 不提供醫療診斷
- 遇到危機狀況時，鼓勵使用者尋求現實中的協助

請用自然、簡潔、溫暖的語氣回應使用者。
```

---

# 14. 測試 Ollama API

確認 Ollama 是否可以正常回應。

可以使用 curl 測試：

```bash
curl http://localhost:11434/api/generate -d "{\"model\":\"llama3.1\",\"prompt\":\"你好，請簡短介紹你自己。\",\"stream\":false}"
```

macOS / Linux 可使用：

```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3.1",
    "prompt": "你好，請簡短介紹你自己。",
    "stream": false
  }'
```

如果使用 `qwen2.5`，請改成：

```json
"model": "qwen2.5"
```

---

# 15. 專案核心流程

本專案流程如下：

```text
使用者傳送 Telegram 訊息
        ↓
telegram_bot.py 接收訊息
        ↓
讀取 persona.md
        ↓
memory.py 取得使用者歷史對話
        ↓
組合 Persona + 歷史訊息 + 使用者新訊息
        ↓
ollama_client.py 呼叫 Ollama API
        ↓
取得模型回覆
        ↓
寫入 SQLite memory.db
        ↓
Telegram Bot 回覆使用者
```

---

# 16. 啟動 Telegram Bot

確定以下條件完成：

- Python 虛擬環境已啟動
- 套件已安裝
- `.env` 已設定
- Ollama 已啟動
- 模型已下載
- Telegram Bot Token 正確

啟動：

```bash
python -m bot.telegram_bot
```

或：

```bash
python bot/telegram_bot.py
```

依照你的專案 import 寫法，兩者可能只有其中一種可用。

---

# 17. 測試機器人

打開 Telegram，找到你建立的 Bot。

輸入：

```text
/start
```

如果正常，Bot 應該會回覆歡迎訊息。

接著可以輸入：

```text
我今天心情有點低落
```

Bot 應該會透過 Ollama 產生情感型回覆。

---

# 18. 常用指令

---

## 18.1 啟動虛擬環境

Windows：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

---

## 18.2 安裝套件

```powershell
pip install -r requirements.txt
```

---

## 18.3 啟動 Ollama 模型

```bash
ollama run llama3.1
```

---

## 18.4 查看 Ollama 模型

```bash
ollama list
```

---

## 18.5 啟動 Telegram Bot

```bash
python -m bot.telegram_bot
```

---

# 19. 測試腳本

如果專案中有 `test.py`，可以執行：

```bash
python test.py
```

建議 `test.py` 用來測試：

- Ollama 是否連線成功
- SQLite 是否能建立資料表
- Persona 是否能讀取
- Bot Token 是否存在

---

# 20. SQLite 資料庫

本專案使用 SQLite 儲存使用者對話記憶。

預設位置：

```text
database/memory.db
```

建議至少包含以下資料：

- 使用者 Telegram ID
- 使用者名稱
- 訊息角色，user / assistant
- 訊息內容
- 建立時間

範例資料表設計：

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 21. 記憶系統說明

`ai/memory.py` 主要負責：

- 儲存使用者訊息
- 儲存 AI 回覆
- 讀取近期對話
- 控制上下文長度
- 避免 prompt 過長

建議每次只取最近幾輪對話，例如最近 10 至 20 則訊息。

---

# 22. Ollama Client 說明

`ai/ollama_client.py` 主要負責呼叫 Ollama API。

Ollama 預設 API：

```text
POST http://localhost:11434/api/generate
```

請求範例：

```json
{
  "model": "llama3.1",
  "prompt": "你好",
  "stream": false
}
```

回應中通常會包含：

```json
{
  "response": "你好，有什麼我可以幫你的嗎？"
}
```

---

# 23. Telegram Bot 說明

`bot/telegram_bot.py` 主要負責：

- 初始化 Telegram Bot
- 註冊 `/start`
- 註冊 `/reset`
- 接收文字訊息
- 呼叫 AI 模組
- 回覆使用者

建議支援指令：

```text
/start  開始使用
/reset  清除對話記憶
/help   查看說明
```

---

# 24. 疑難排解

---

## 24.1 Telegram Bot 沒有回覆

請檢查：

1. Bot 是否正在執行
2. `.env` 裡面的 `TELEGRAM_BOT_TOKEN` 是否正確
3. 是否有安裝 `python-telegram-bot`
4. 終端機是否有錯誤訊息

---

## 24.2 Ollama 無法連線

請確認 Ollama 是否啟動：

```bash
ollama list
```

或開啟：

```text
http://localhost:11434
```

如果沒有啟動，可以重新開啟 Ollama App，或執行：

```bash
ollama serve
```

---

## 24.3 模型不存在

如果出現類似：

```text
model not found
```

請先下載模型：

```bash
ollama pull llama3.1
```

或確認 `.env` 裡的模型名稱與 `ollama list` 顯示一致。

---

## 24.4 Python 找不到模組

例如：

```text
ModuleNotFoundError
```

請確認虛擬環境有啟動，並重新安裝套件：

```bash
pip install -r requirements.txt
```

或：

```bash
pip install python-telegram-bot==20.8 requests python-dotenv
```

---

## 24.5 PowerShell 無法啟動虛擬環境

如果 Windows PowerShell 出現執行權限問題，執行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然後重新啟動虛擬環境：

```powershell
.venv\Scripts\activate
```

---

# 25. 安全注意事項

請勿將以下資料上傳到 GitHub：

- `.env`
- Telegram Bot Token
- 使用者對話資料庫
- 個人敏感資料
- log 中可能包含的使用者訊息

建議建立 `.gitignore`：

```gitignore
.venv/
__pycache__/
*.pyc
.env
database/*.db
logs/
```

---

# 26. 建議開發路線

未來可以加入：

- 情緒分類
- 使用者長期偏好記憶
- 對話摘要
- 多模型切換
- Web 管理介面
- 記憶清除功能
- 使用者黑名單
- 回覆串流輸出
- Docker 部署
- systemd 背景服務
- 更完整的 logging 系統

---

# 27. 專案啟動懶人包

如果你已經完成所有設定，下次只需要：

## Windows

```bash
cd EmotionalAI
.venv\Scripts\activate
ollama list
python -m bot.telegram_bot
```

## macOS / Linux

```bash
cd EmotionalAI
source .venv/bin/activate
ollama list
python -m bot.telegram_bot
```

---

# 28. 授權

本專案目前尚未指定授權條款。  
如果要開源，建議加入 MIT License。

---

# 29. 聲明

EmotionalAI 是一個情感陪伴型 AI 專案，不是心理治療、醫療診斷或危機干預工具。

如果使用者出現自傷、傷人或緊急危機狀況，應立即建議使用者聯絡當地緊急服務、可信任的人，或專業心理健康資源。

---
