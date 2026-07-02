import json

from db.connection import get_conn, now


# =========================
# JSON TEXT 工具
# =========================

def _loads_list(value):
  """
  將資料庫中的 TEXT 轉成 list。

  支援：
  1. None -> []
  2. JSON list 字串 -> list
  3. 一般字串 -> [字串]
  """

  if not value:
    return []

  if isinstance(value, list):
    return value

  try:
    data = json.loads(value)
    if isinstance(data, list):
      return data
    if isinstance(data, str):
      return [data]
    return []
  except Exception:
    return [str(value)]


def _dumps_list(items):
  """
  將 list 轉成 JSON 字串。
  """

  if not items:
    return None

  cleaned = []

  for item in items:
    if item is None:
      continue

    text = str(item).strip()

    if not text:
      continue

    if text not in cleaned:
      cleaned.append(text)

  if not cleaned:
    return None

  return json.dumps(cleaned, ensure_ascii=False)


def _merge_text_list(old_value, new_items):
  """
  將舊 TEXT JSON list 與新資料合併去重。
  """

  old_items = _loads_list(old_value)

  if isinstance(new_items, str):
    new_items = [new_items]

  new_items = new_items or []

  merged = []

  for item in old_items + new_items:
    if item is None:
      continue

    text = str(item).strip()

    if not text:
      continue

    if text not in merged:
      merged.append(text)

  return _dumps_list(merged)


def _remove_text_list_items(old_value, remove_items):
  """
  從 TEXT JSON list 裡移除指定項目。
  """

  old_items = _loads_list(old_value)

  if isinstance(remove_items, str):
    remove_items = [remove_items]

  remove_items = set(str(x).strip() for x in remove_items if str(x).strip())

  remaining = []

  for item in old_items:
    if item not in remove_items:
      remaining.append(item)

  return _dumps_list(remaining)


def _profile_row_to_dict(row):
  """
  user_profiles row -> dict
  """

  if not row:
    return None

  return {
    "id": row["id"],
    "user_id": row["user_id"],
    "preferred_name": row["preferred_name"],
    "real_name": row["real_name"],
    "interests": _loads_list(row["interests"]),
    "likes": _loads_list(row["likes"]),
    "dislikes": _loads_list(row["dislikes"]),
    "important_facts": _loads_list(row["important_facts"]),
    "boundaries": _loads_list(row["boundaries"]),
    "language_preference": row["language_preference"],
    "created_at": row["created_at"],
    "updated_at": row["updated_at"],
  }


def _user_character_profile_row_to_dict(row):
  """
  user_character_profiles row -> dict
  """

  if not row:
    return None

  return {
    "id": row["id"],
    "user_id": row["user_id"],
    "character_id": row["character_id"],
    "nickname_for_user": row["nickname_for_user"],
    "nickname_for_ai": row["nickname_for_ai"],
    "relationship_mode": row["relationship_mode"],
    "tone_preference": row["tone_preference"],
    "intimacy_level": row["intimacy_level"],
    "roleplay_boundaries": row["roleplay_boundaries"],
    "custom_instructions": row["custom_instructions"],
    "created_at": row["created_at"],
    "updated_at": row["updated_at"],
  }


# =========================
# user_profiles
# =========================

def ensure_user_profile(user_id: str):
  """
  確保 user_profiles 有這個 user_id 的資料列。

  如果不存在就建立一筆空資料。
  """

  user_id = str(user_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT *
  FROM user_profiles
  WHERE user_id = ?
  LIMIT 1
  """, (user_id,))

  row = cursor.fetchone()

  if row:
    conn.close()
    return _profile_row_to_dict(row)

  timestamp = now()

  cursor.execute("""
  INSERT INTO user_profiles (
    user_id,
    language_preference,
    created_at,
    updated_at
  )
  VALUES (?, ?, ?, ?)
  """, (
    user_id,
    "繁體中文",
    timestamp,
    timestamp
  ))

  conn.commit()

  cursor.execute("""
  SELECT *
  FROM user_profiles
  WHERE user_id = ?
  LIMIT 1
  """, (user_id,))

  row = cursor.fetchone()
  conn.close()

  return _profile_row_to_dict(row)


def get_user_profile(user_id: str):
  """
  取得使用者基本資料。
  如果不存在，回傳 None。
  """

  user_id = str(user_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT *
  FROM user_profiles
  WHERE user_id = ?
  LIMIT 1
  """, (user_id,))

  row = cursor.fetchone()
  conn.close()

  return _profile_row_to_dict(row)


def update_user_profile(
  user_id: str,
  preferred_name=None,
  real_name=None,
  interests=None,
  likes=None,
  dislikes=None,
  important_facts=None,
  boundaries=None,
  language_preference=None,
):
  """
  更新使用者基本資料。

  規則：
  - preferred_name / real_name / language_preference：直接覆蓋
  - interests / likes / dislikes / important_facts / boundaries：合併去重
  """

  user_id = str(user_id)

  ensure_user_profile(user_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT *
  FROM user_profiles
  WHERE user_id = ?
  LIMIT 1
  """, (user_id,))

  row = cursor.fetchone()

  if not row:
    conn.close()
    return None

  new_interests = _merge_text_list(row["interests"], interests)
  new_likes = _merge_text_list(row["likes"], likes)
  new_dislikes = _merge_text_list(row["dislikes"], dislikes)
  new_important_facts = _merge_text_list(row["important_facts"], important_facts)
  new_boundaries = _merge_text_list(row["boundaries"], boundaries)

  cursor.execute("""
  UPDATE user_profiles
  SET
    preferred_name = COALESCE(?, preferred_name),
    real_name = COALESCE(?, real_name),
    interests = ?,
    likes = ?,
    dislikes = ?,
    important_facts = ?,
    boundaries = ?,
    language_preference = COALESCE(?, language_preference),
    updated_at = ?
  WHERE user_id = ?
  """, (
    preferred_name,
    real_name,
    new_interests,
    new_likes,
    new_dislikes,
    new_important_facts,
    new_boundaries,
    language_preference,
    now(),
    user_id
  ))

  conn.commit()
  conn.close()

  return get_user_profile(user_id)


def replace_user_profile_field(user_id: str, field_name: str, value):
  """
  直接覆蓋 user_profiles 的指定欄位。

  可用欄位：
  - preferred_name
  - real_name
  - interests
  - likes
  - dislikes
  - important_facts
  - boundaries
  - language_preference

  注意：
  list 類欄位會自動轉 JSON。
  """

  allowed_fields = {
    "preferred_name",
    "real_name",
    "interests",
    "likes",
    "dislikes",
    "important_facts",
    "boundaries",
    "language_preference",
  }

  if field_name not in allowed_fields:
    raise ValueError(f"不允許更新 user_profiles 欄位：{field_name}")

  user_id = str(user_id)
  ensure_user_profile(user_id)

  if field_name in {
    "interests",
    "likes",
    "dislikes",
    "important_facts",
    "boundaries",
  }:
    if isinstance(value, str):
      value = [value]
    value = _dumps_list(value)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute(f"""
  UPDATE user_profiles
  SET {field_name} = ?,
    updated_at = ?
  WHERE user_id = ?
  """, (
    value,
    now(),
    user_id
  ))

  conn.commit()
  conn.close()

  return get_user_profile(user_id)


def remove_user_profile_items(user_id: str, field_name: str, items):
  """
  從 user_profiles 的 list 欄位移除項目。

  可用欄位：
  - interests
  - likes
  - dislikes
  - important_facts
  - boundaries
  """

  allowed_fields = {
    "interests",
    "likes",
    "dislikes",
    "important_facts",
    "boundaries",
  }

  if field_name not in allowed_fields:
    raise ValueError(f"此欄位不支援項目移除：{field_name}")

  user_id = str(user_id)
  profile = ensure_user_profile(user_id)

  old_value = json.dumps(profile[field_name], ensure_ascii=False)
  new_value = _remove_text_list_items(old_value, items)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute(f"""
  UPDATE user_profiles
  SET {field_name} = ?,
    updated_at = ?
  WHERE user_id = ?
  """, (
    new_value,
    now(),
    user_id
  ))

  conn.commit()
  conn.close()

  return get_user_profile(user_id)


# =========================
# user_character_profiles
# =========================

def ensure_user_character_profile(user_id: str, character_id: int):
  """
  確保 user_character_profiles 有 user_id + character_id 的資料列。

  如果不存在就建立一筆空資料。
  """

  user_id = str(user_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT *
  FROM user_character_profiles
  WHERE user_id = ?
    AND character_id = ?
  LIMIT 1
  """, (
    user_id,
    character_id
  ))

  row = cursor.fetchone()

  if row:
    conn.close()
    return _user_character_profile_row_to_dict(row)

  timestamp = now()

  cursor.execute("""
  INSERT INTO user_character_profiles (
    user_id,
    character_id,
    created_at,
    updated_at
  )
  VALUES (?, ?, ?, ?)
  """, (
    user_id,
    character_id,
    timestamp,
    timestamp
  ))

  conn.commit()

  cursor.execute("""
  SELECT *
  FROM user_character_profiles
  WHERE user_id = ?
    AND character_id = ?
  LIMIT 1
  """, (
    user_id,
    character_id
  ))

  row = cursor.fetchone()
  conn.close()

  return _user_character_profile_row_to_dict(row)


def get_user_character_profile(user_id: str, character_id: int):
  """
  取得某使用者對某 AI 角色的專屬設定。
  如果不存在，回傳 None。
  """

  user_id = str(user_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  SELECT *
  FROM user_character_profiles
  WHERE user_id = ?
    AND character_id = ?
  LIMIT 1
  """, (
    user_id,
    character_id
  ))

  row = cursor.fetchone()
  conn.close()

  return _user_character_profile_row_to_dict(row)


def update_user_character_profile(
  user_id: str,
  character_id: int,
  nickname_for_user=None,
  nickname_for_ai=None,
  relationship_mode=None,
  tone_preference=None,
  intimacy_level=None,
  roleplay_boundaries=None,
  custom_instructions=None,
):
  """
  更新 user_character_profiles。

  規則：
  - 傳入 None 的欄位不更新
  - 傳入空字串 "" 代表清空欄位
  - intimacy_level 建議範圍 0~5
  """

  user_id = str(user_id)

  ensure_user_character_profile(user_id, character_id)

  if intimacy_level is not None:
    try:
      intimacy_level = int(intimacy_level)
    except Exception:
      intimacy_level = 0

    intimacy_level = max(0, min(5, intimacy_level))

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute("""
  UPDATE user_character_profiles
  SET
    nickname_for_user = CASE WHEN ? IS NOT NULL THEN ? ELSE nickname_for_user END,
    nickname_for_ai = CASE WHEN ? IS NOT NULL THEN ? ELSE nickname_for_ai END,
    relationship_mode = CASE WHEN ? IS NOT NULL THEN ? ELSE relationship_mode END,
    tone_preference = CASE WHEN ? IS NOT NULL THEN ? ELSE tone_preference END,
    intimacy_level = CASE WHEN ? IS NOT NULL THEN ? ELSE intimacy_level END,
    roleplay_boundaries = CASE WHEN ? IS NOT NULL THEN ? ELSE roleplay_boundaries END,
    custom_instructions = CASE WHEN ? IS NOT NULL THEN ? ELSE custom_instructions END,
    updated_at = ?
  WHERE user_id = ?
    AND character_id = ?
  """, (
    nickname_for_user, nickname_for_user,
    nickname_for_ai, nickname_for_ai,
    relationship_mode, relationship_mode,
    tone_preference, tone_preference,
    intimacy_level, intimacy_level,
    roleplay_boundaries, roleplay_boundaries,
    custom_instructions, custom_instructions,
    now(),
    user_id,
    character_id
  ))

  conn.commit()
  conn.close()

  return get_user_character_profile(user_id, character_id)


def clear_user_character_field(user_id: str, character_id: int, field_name: str):
  """
  清空 user_character_profiles 的指定欄位。

  可用欄位：
  - nickname_for_user
  - nickname_for_ai
  - relationship_mode
  - tone_preference
  - roleplay_boundaries
  - custom_instructions
  """

  allowed_fields = {
    "nickname_for_user",
    "nickname_for_ai",
    "relationship_mode",
    "tone_preference",
    "roleplay_boundaries",
    "custom_instructions",
  }

  if field_name not in allowed_fields:
    raise ValueError(f"不允許清空 user_character_profiles 欄位：{field_name}")

  user_id = str(user_id)
  ensure_user_character_profile(user_id, character_id)

  conn = get_conn()
  cursor = conn.cursor()

  cursor.execute(f"""
  UPDATE user_character_profiles
  SET {field_name} = NULL,
    updated_at = ?
  WHERE user_id = ?
    AND character_id = ?
  """, (
    now(),
    user_id,
    character_id
  ))

  conn.commit()
  conn.close()

  return get_user_character_profile(user_id, character_id)


# =========================
# context 格式化
# =========================

def format_user_profile_for_prompt(profile: dict):
  """
  將 user_profile 格式化成 prompt 可讀文字。
  """

  if not profile:
    return "目前沒有使用者基本資料。"

  lines = []

  if profile.get("preferred_name"):
    lines.append(f"使用者偏好名稱：{profile['preferred_name']}")

  if profile.get("real_name"):
    lines.append(f"使用者真實姓名：{profile['real_name']}")

  if profile.get("interests"):
    lines.append("使用者興趣：" + "、".join(profile["interests"]))

  if profile.get("likes"):
    lines.append("使用者喜歡：" + "、".join(profile["likes"]))

  if profile.get("dislikes"):
    lines.append("使用者不喜歡或討厭：" + "、".join(profile["dislikes"]))

  if profile.get("important_facts"):
    lines.append("使用者重要事實：" + "、".join(profile["important_facts"]))

  if profile.get("boundaries"):
    lines.append("使用者界線：" + "、".join(profile["boundaries"]))

  if profile.get("language_preference"):
    lines.append(f"語言偏好：{profile['language_preference']}")

  if not lines:
    return "目前沒有使用者基本資料。"

  return "\n".join(f"- {line}" for line in lines)


def format_user_character_profile_for_prompt(profile: dict):
  """
  將 user_character_profile 格式化成 prompt 可讀文字。
  """

  if not profile:
    return "目前沒有此使用者對目前 AI 角色的專屬設定。"

  lines = []

  if profile.get("nickname_for_user"):
    lines.append(f"目前 AI 角色應稱呼使用者為：{profile['nickname_for_user']}")

  if profile.get("nickname_for_ai"):
    lines.append(f"使用者稱呼目前 AI 角色為：{profile['nickname_for_ai']}")

  if profile.get("relationship_mode"):
    lines.append(f"關係模式：{profile['relationship_mode']}")

  if profile.get("tone_preference"):
    lines.append(f"語氣偏好：{profile['tone_preference']}")

  if profile.get("intimacy_level") is not None:
    lines.append(f"親密度等級：{profile['intimacy_level']} / 5")

  if profile.get("roleplay_boundaries"):
    lines.append(f"角色互動界線：{profile['roleplay_boundaries']}")

  if profile.get("custom_instructions"):
    lines.append(f"此使用者對目前 AI 角色的自訂指令：{profile['custom_instructions']}")

  if not lines:
    return "目前沒有此使用者對目前 AI 角色的專屬設定。"

  return "\n".join(f"- {line}" for line in lines)


# =========================
# debug / 測試輔助
# =========================

def debug_get_profile_bundle(user_id: str, character_id: int):
  """
  測試用：一次取得 user_profile + user_character_profile。
  """

  return {
    "user_profile": get_user_profile(user_id),
    "user_character_profile": get_user_character_profile(user_id, character_id)
  }
