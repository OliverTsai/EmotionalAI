import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = "database/memory.db"


def now():
  return datetime.now().isoformat(timespec="seconds")


def get_conn():
  """
  建立 SQLite 連線。

  注意：
  - database/ 是存放實際 memory.db 的資料夾
  - db/ 是 Python 程式模組資料夾
  """

  Path("database").mkdir(exist_ok=True)

  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row

  # 建議打開 foreign key 支援
  conn.execute("PRAGMA foreign_keys = ON")

  # 對 SQLite 讀寫穩定性較好，尤其未來邊測邊查資料庫
  conn.execute("PRAGMA journal_mode = WAL")

  return conn
