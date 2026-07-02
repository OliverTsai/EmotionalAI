from db.connection import get_conn, now

DEFAULT_CHARACTER_KEY = "yaling"
# DEFAULT_CHARACTER_KEY = "planner"


def get_character_by_key(character_key: str = DEFAULT_CHARACTER_KEY):
  """
  用 character_key 取得 AI 角色資料。

  例如：
  - yaling
  - planner
  - frontend_engineer

  回傳 dict 或 None。
  """

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT
    id,
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
  FROM characters
  WHERE character_key = ?
    AND is_active = 1
  LIMIT 1
  """, (character_key,))

  row = cursor.fetchone()
  conn.close()

  if not row:
    return None

  return dict(row)


def get_default_character():
  """
  取得預設 AI 角色。
  目前預設是雅鈴。
  """

  return get_character_by_key(DEFAULT_CHARACTER_KEY)


def get_character_id_by_key(character_key: str = DEFAULT_CHARACTER_KEY):
  """
  只取得 character_id。
  """

  character = get_character_by_key(character_key)

  if not character:
    raise ValueError(f"找不到 AI 角色：{character_key}")

  return character["id"]


def list_characters():
  """
  列出所有啟用中的 AI 角色。
  未來可用於 /characters 指令。
  """

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT
    id,
    character_key,
    name,
    gender,
    character_type,
    default_persona,
    default_speaking_style,
    default_boundaries
  FROM characters
  WHERE is_active = 1
  ORDER BY id ASC
  """)

  rows = cursor.fetchall()
  conn.close()

  return [dict(row) for row in rows]


def ensure_character(character_key: str = DEFAULT_CHARACTER_KEY):
  """
  確保角色存在。
  如果角色不存在，直接丟出錯誤。
  """

  character = get_character_by_key(character_key)

  if not character:
    raise ValueError(
      f"找不到 character_key={character_key} 的 AI 角色。"
      "請先執行 python -m db.schema 初始化資料庫。"
    )

  return character
