from db.connection import get_conn, now

def init_db():
  """
  初始化資料庫結構。

  目前包含：
  1. users：平台使用者對應資料，預留給 Telegram / Discord / Web
  2. characters：AI 角色資料
  3. user_profiles：使用者自己的基本資料
  4. user_character_profiles：某使用者對某 AI 角色的專屬互動設定
  5. conversations：對話串
  6. message_logs：聊天紀錄
  7. memories：長期記憶
  8. entities：實體
  9. entity_relations：實體關係
  """

  conn = get_conn()
  cursor = conn.cursor()

  # =========================
  # users
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL DEFAULT 'telegram',
    platform_user_id TEXT NOT NULL,
    username TEXT,
    display_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(platform, platform_user_id)
  )
  """)

  # =========================
  # characters
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    gender TEXT,
    character_type TEXT NOT NULL DEFAULT 'companion',
    default_persona TEXT,
    default_speaking_style TEXT,
    default_boundaries TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )
  """)

  # =========================
  # user_profiles
  # 使用者自己的資料，不綁定特定 AI 角色
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    preferred_name TEXT,
    real_name TEXT,
    interests TEXT,
    likes TEXT,
    dislikes TEXT,
    important_facts TEXT,
    boundaries TEXT,
    language_preference TEXT DEFAULT '繁體中文',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id)
  )
  """)

  # =========================
  # user_character_profiles
  # 某使用者 × 某 AI 角色 的專屬設定
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS user_character_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER NOT NULL,
    nickname_for_user TEXT,
    nickname_for_ai TEXT,
    relationship_mode TEXT,
    tone_preference TEXT,
    intimacy_level INTEGER DEFAULT 0,
    roleplay_boundaries TEXT,
    custom_instructions TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, character_id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
  )
  """)

  # =========================
  # conversations
  # 預留給未來多角色、多對話串
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER NOT NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id)
  )
  """)

  # =========================
  # message_logs
  # 原始聊天紀錄
  # 目前保留舊欄位 user_id/role/content，新增 character_id/conversation_id
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS message_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER,
    conversation_id INTEGER,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
  )
  """)

  # =========================
  # memories
  # 長期記憶條目
  # 新增 character_id 與 scope，支援：
  # - user_global
  # - user_character
  # - character_global
  # - project
  # - task
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER,
    scope TEXT NOT NULL DEFAULT 'user_global',
    memory_type TEXT NOT NULL,
    subject TEXT,
    predicate TEXT,
    object TEXT,
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 1,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed_at TEXT,
    access_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (character_id) REFERENCES characters(id)
  )
  """)

  # =========================
  # entities
  # 實體：人、事、物、地點、概念
  # 目前新增 character_id，避免不同角色語境互相污染
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    alias TEXT,
    description TEXT,
    attributes_json TEXT,
    importance INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, character_id, entity_type, name),
    FOREIGN KEY (character_id) REFERENCES characters(id)
  )
  """)

  # =========================
  # entity_relations
  # 實體關係
  # =========================
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS entity_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    character_id INTEGER,
    from_entity_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    to_entity_id INTEGER NOT NULL,
    description TEXT,
    importance INTEGER DEFAULT 1,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id),
    FOREIGN KEY (from_entity_id) REFERENCES entities(id),
    FOREIGN KEY (to_entity_id) REFERENCES entities(id)
  )
  """)

  # =========================
  # indexes
  # =========================

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_users_platform_user_id
  ON users(platform, platform_user_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_characters_key
  ON characters(character_key)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id
  ON user_profiles(user_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_user_character_profiles_user_character
  ON user_character_profiles(user_id, character_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_conversations_user_character
  ON conversations(user_id, character_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_message_logs_user_id
  ON message_logs(user_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_message_logs_user_character
  ON message_logs(user_id, character_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_memories_user_id
  ON memories(user_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_memories_user_character
  ON memories(user_id, character_id)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_memories_scope
  ON memories(scope)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_memories_type
  ON memories(memory_type)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_entities_user_character_type_name
  ON entities(user_id, character_id, entity_type, name)
  """)

  cursor.execute("""
  CREATE INDEX IF NOT EXISTS idx_entity_relations_user_character
  ON entity_relations(user_id, character_id)
  """)

  # =========================
  # seed default characters
  # =========================
  seed_default_characters(cursor)

  conn.commit()
  conn.close()


def seed_default_characters(cursor):
  """
  建立預設 AI 角色。

  注意：
  使用 INSERT OR IGNORE，避免每次啟動重複新增。
  """

  timestamp = now()

  cursor.execute("""
  INSERT OR IGNORE INTO characters (
    character_key,
    name,
    gender,
    character_type,
    default_persona,
    default_speaking_style,
    default_boundaries,
    is_active,
    created_at,
    updated_at
  )
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """, (
    "yaling",
    "雅鈴",
    "female",
    "companion",
    "你是雅鈴，一個溫柔、有同理心、使用繁體中文的情感陪伴型 AI。",
    "自然、溫柔、親近，但不要過度裝熟。稱呼與親密程度必須依照目前使用者對雅鈴的個人設定。",
    "不得把其他使用者的名字、稱呼、興趣、喜好或討厭事項套用到目前使用者身上。",
    1,
    timestamp,
    timestamp
  ))

  cursor.execute("""
  INSERT OR IGNORE INTO characters (
    character_key,
    name,
    gender,
    character_type,
    default_persona,
    default_speaking_style,
    default_boundaries,
    is_active,
    created_at,
    updated_at
  )
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """, (
    "planner",
    "企劃助理",
    "neutral",
    "planner",
    "你是一個擅長需求拆解、企劃整理、架構規劃的功能型 AI。",
    "清楚、條列、務實、先整理目標再提出步驟。",
    "不要使用陪伴型角色的親密稱呼，除非使用者對此角色有明確設定。",
    1,
    timestamp,
    timestamp
  ))

  cursor.execute("""
  INSERT OR IGNORE INTO characters (
    character_key,
    name,
    gender,
    character_type,
    default_persona,
    default_speaking_style,
    default_boundaries,
    is_active,
    created_at,
    updated_at
  )
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """, (
    "frontend_engineer",
    "前端工程師",
    "neutral",
    "engineer",
    "你是一個資深前端工程師 AI，擅長 React、Tailwind、前端架構與可維護程式碼。",
    "專業、直接、重視可執行方案。必要時提供程式碼與檔案結構。",
    "不要套用情感陪伴型角色的語氣與稱呼，除非使用者對此角色有明確設定。",
    1,
    timestamp,
    timestamp
  ))


if __name__ == "__main__":
  init_db()
  print("資料庫初始化完成")
