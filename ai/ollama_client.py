import requests
import logging
from pathlib import Path

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, PERSONA_PATH

from db.schema import init_db
from ai.characters import ensure_character, DEFAULT_CHARACTER_KEY
from ai.memory import (
    save_message,
    get_recent_memory,
    get_long_term_memory,
    search_memories,
    save_memory,
    upsert_entity,
)

from ai.profiles import (
    ensure_user_profile,
    get_user_profile,
    update_user_profile,
    ensure_user_character_profile,
    get_user_character_profile,
    update_user_character_profile,
    format_user_profile_for_prompt,
    format_user_character_profile_for_prompt,
)


# =========================
# logging
# =========================

Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

if not logger.handlers:
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("logs/ollama_client.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


# =========================
# Ollama 設定
# =========================

MODEL = OLLAMA_MODEL


def get_ollama_chat_url():
    """
    兼容兩種 config 寫法：

    1. OLLAMA_BASE_URL = "http://localhost:11434"
       會自動變成 http://localhost:11434/api/chat

    2. OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
       會直接使用
    """

    base = str(OLLAMA_BASE_URL).rstrip("/")

    if base.endswith("/api/chat"):
        return base

    return base + "/api/chat"


OLLAMA_CHAT_URL = get_ollama_chat_url()


# =========================
# Persona
# =========================

def load_base_persona():
    """
    載入 persona.md。

    注意：
    persona.md 只能放「通用 AI 行為規則」或「基礎人格」。
    不要放特定使用者資料，例如：
    - 使用者叫阿哲
    - 要叫使用者哥哥
    - 使用者喜歡 AI / 哲學

    這些應該放在 user_profiles / user_character_profiles / memories。
    """

    try:
        if PERSONA_PATH and PERSONA_PATH.exists():
            text = PERSONA_PATH.read_text(encoding="utf-8")
            logger.info(f"已載入 persona.md：{PERSONA_PATH.resolve()}")
            return text.strip()
    except Exception as e:
        logger.warning(f"讀取 persona.md 失敗：{e}")

    logger.info("找不到 persona.md，使用預設 persona")

    return "你是一個溫柔、有同理心的中文 AI。請使用繁體中文回覆。"


BASE_PERSONA = load_base_persona()


# =========================
# 系統規則
# =========================

SYSTEM_ISOLATION_RULES = """
【最高優先規則：多使用者與多角色隔離】

1. 你只能使用目前 user_id 與目前 character_id 允許使用的資料。
2. 不得把其他使用者的名字、稱呼、興趣、喜好、討厭事項、關係設定套用到目前使用者。
3. 不得把其他 AI 角色與使用者的互動設定套用到目前角色。
4. 如果目前資料中沒有某項資訊，必須承認不知道，不可猜測。
5. 使用者對目前 AI 角色的專屬設定，優先於 AI 角色預設人格。
6. 使用者全域資料只描述使用者本身，不代表所有 AI 角色都要用同一種態度對待他。
7. 角色專屬記憶只能在目前 character_id 相符時使用。
8. 你必須使用繁體中文回覆，除非使用者明確要求其他語言。
9. 不要在回覆中提到內部欄位名稱，例如 user_id、character_id、scope，除非使用者正在詢問技術細節。
"""


# =========================
# context / prompt
# =========================

def build_context(
    user_id: str,
    message: str,
    character_id=None,
    recent_limit: int = 8,
    long_limit: int = 16,
    related_limit: int = 8,
):
    """
    建立給 AI 使用的記憶資料。

    隔離核心：
    1. user_profile：
       - 只查目前 user_id

    2. user_character_profile：
       - 只查目前 user_id + character_id

    3. 最近對話：
       - 只查目前 user_id + character_id

    4. 長期記憶：
       - user_global：目前 user_id 可用
       - user_character：必須同時符合目前 user_id + character_id

    5. 相關記憶：
       - 同上
    """

    # 確保 profile 資料列存在
    ensure_user_profile(user_id)

    if character_id is not None:
        ensure_user_character_profile(user_id, character_id)

    user_profile = get_user_profile(user_id)

    user_character_profile = None
    if character_id is not None:
        user_character_profile = get_user_character_profile(user_id, character_id)

    recent_messages = get_recent_memory(
        user_id=user_id,
        limit=recent_limit,
        character_id=character_id
    )

    long_term_memories = get_long_term_memory(
        user_id=user_id,
        limit=long_limit,
        character_id=character_id
    )

    related_memories = search_memories(
        user_id=user_id,
        query=message,
        limit=related_limit,
        character_id=character_id
    )

    logger.info(
        f"[build_context] user_id={user_id} character_id={character_id} "
        f"profile={'yes' if user_profile else 'no'} "
        f"user_character_profile={'yes' if user_character_profile else 'no'} "
        f"recent={len(recent_messages)} long={len(long_term_memories)} related={len(related_memories)}"
    )

    return {
        "user_profile": user_profile,
        "user_character_profile": user_character_profile,
        "recent_messages": recent_messages,
        "long_term_memories": long_term_memories,
        "related_memories": related_memories,
    }



def build_messages(
    user_id: str,
    character: dict,
    user_message: str,
    context: dict,
):
    """
    建立 Ollama /api/chat 使用的 messages。
    """

    character_id = character["id"]

    character_block = f"""
【目前 AI 角色】
角色 ID：{character_id}
角色代號：{character.get("character_key") or ""}
角色名稱：{character.get("name") or ""}
性別設定：{character.get("gender") or ""}
角色類型：{character.get("character_type") or ""}

【角色預設人格】
{character.get("default_persona") or "未設定"}

【角色預設語氣】
{character.get("default_speaking_style") or "未設定"}

【角色預設界線】
{character.get("default_boundaries") or "未設定"}
""".strip()

    current_identity_block = f"""
【目前請求身分】
目前 user_id：{user_id}
目前 character_id：{character_id}

注意：
以下記憶與最近對話已由系統依照 user_id 與 character_id 過濾。
你只能使用下方提供的資料，不可引用其他使用者或其他角色的資料。
""".strip()

    user_profile = context.get("user_profile")
    user_character_profile = context.get("user_character_profile")

    user_profile_text = format_user_profile_for_prompt(user_profile)
    user_character_profile_text = format_user_character_profile_for_prompt(user_character_profile)

    profile_block = f"""
【使用者基本資料】
{user_profile_text}

【此使用者對目前 AI 角色的專屬設定】
{user_character_profile_text}

注意：
- 使用者基本資料只描述目前使用者本人。
- 此使用者對目前 AI 角色的專屬設定，優先於角色預設人格與語氣。
- 若專屬設定中指定稱呼，必須優先使用該稱呼。
""".strip()

    long_term_memories = context.get("long_term_memories") or []
    related_memories = context.get("related_memories") or []
    recent_messages = context.get("recent_messages") or []

    memory_lines = []

    memory_lines.append("【長期記憶】")
    if long_term_memories:
        for memory in long_term_memories:
            memory_lines.append(f"- {memory}")
    else:
        memory_lines.append("- 目前沒有可用的長期記憶。")

    memory_lines.append("")
    memory_lines.append("【與本次訊息相關的記憶】")
    if related_memories:
        for memory in related_memories:
            memory_lines.append(f"- {memory}")
    else:
        memory_lines.append("- 目前沒有找到相關記憶。")

    memory_block = "\n".join(memory_lines)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_ISOLATION_RULES.strip()
        },
        {
            "role": "system",
            "content": BASE_PERSONA.strip()
        },
        {
            "role": "system",
            "content": character_block
        },
        {
            "role": "system",
            "content": current_identity_block
        },
        {
            "role": "system",
            "content": profile_block
        },
        {
            "role": "system",
            "content": memory_block
        },
    ]

    # 加入最近對話
    for role, content in recent_messages:
        if role not in ("user", "assistant", "system"):
            continue

        messages.append({
            "role": role,
            "content": content
        })

    # 加入當前訊息
    messages.append({
        "role": "user",
        "content": user_message
    })

    return messages


# =========================
# 簡易記憶抽取工具
# =========================

def cut_first_phrase(text: str):
    """
    取第一個短語，避免把後半句一起存進名字或偏好。
    """

    if not text:
        return ""

    separators = [
        "，",
        "。",
        ",",
        ".",
        "！",
        "!",
        "？",
        "?",
        "、",
        "\n",
    ]

    result = text.strip()

    for sep in separators:
        if sep in result:
            result = result.split(sep, 1)[0].strip()

    return result.strip()


def extract_after_keywords(text: str, keywords):
    """
    從文字中找第一個符合的 keyword，回傳 keyword 後面的短片段。
    """

    for keyword in keywords:
        if keyword in text:
            return cut_first_phrase(text.split(keyword, 1)[1])

    return None


def extract_memory_intent(user_message: str):
    """
    簡單判斷是否可能包含值得記憶的資訊。
    """

    keywords = [
        "記住",
        "你要記得",
        "不要忘記",
        "我的",
        "我叫",
        "我的名字是",
        "我是",
        "生日",
        "喜歡",
        "討厭",
        "不喜歡",
        "我住",
        "我家",
        "我朋友",
        "我女友",
        "我男友",
        "我女朋友",
        "我男朋友",
        "我老婆",
        "我老公",
        "叫我",
        "稱呼我",
        "以後叫我",
        "請叫我",
        "你可以叫我",
        "人格",
        "關係",
        "語氣",
        "陪我",
    ]

    return any(k in user_message for k in keywords)


def simple_memory_extract(user_id: str, message: str, character_id=None):
    """
    規則型記憶抽取。

    現在優先寫入：
    - user_profiles
    - user_character_profiles

    並保留少量 memories 作為補充記憶。
    """

    text = message.strip()
    extracted_count = 0

    ensure_user_profile(user_id)

    if character_id is not None:
        ensure_user_character_profile(user_id, character_id)

    # -------------------------
    # 使用者名字：user_profiles.preferred_name
    # -------------------------
    name = extract_after_keywords(text, ["我叫", "我的名字是"])
    if name and len(name) <= 20:
        update_user_profile(
            user_id=user_id,
            preferred_name=name
        )

        # 補充 entity
        upsert_entity(
            user_id=user_id,
            character_id=None,
            entity_type="person",
            name=name,
            description="使用者本人",
            importance=5
        )

        extracted_count += 1
        logger.info(f"[profile_extract] user_id={user_id} preferred_name={name}")

    # -------------------------
    # 喜歡 / 興趣：user_profiles.interests + likes
    # -------------------------
    like_obj = extract_after_keywords(
        text,
        ["我喜歡", "我的興趣是", "我有興趣的是"]
    )

    if like_obj and len(like_obj) <= 80:
        update_user_profile(
            user_id=user_id,
            interests=[like_obj],
            likes=[like_obj]
        )

        upsert_entity(
            user_id=user_id,
            character_id=None,
            entity_type="concept",
            name=like_obj,
            description=f"使用者喜歡的事物或風格：{like_obj}",
            importance=2
        )

        extracted_count += 1
        logger.info(f"[profile_extract] user_id={user_id} like={like_obj}")

    # -------------------------
    # 不喜歡 / 討厭：user_profiles.dislikes
    # -------------------------
    dislike_obj = extract_after_keywords(
        text,
        ["我不喜歡", "我討厭", "我很討厭"]
    )

    if dislike_obj and len(dislike_obj) <= 80:
        update_user_profile(
            user_id=user_id,
            dislikes=[dislike_obj]
        )

        upsert_entity(
            user_id=user_id,
            character_id=None,
            entity_type="concept",
            name=dislike_obj,
            description=f"使用者不喜歡或討厭的事物：{dislike_obj}",
            importance=2
        )

        extracted_count += 1
        logger.info(f"[profile_extract] user_id={user_id} dislike={dislike_obj}")

    # -------------------------
    # 關係資料：先放 important_facts
    # -------------------------
    relationship_patterns = [
        ("我女朋友叫", "使用者的女朋友"),
        ("我男朋友叫", "使用者的男朋友"),
        ("我老婆叫", "使用者的老婆"),
        ("我老公叫", "使用者的老公"),
    ]

    for pattern, relation_name in relationship_patterns:
        if pattern in text:
            person_name = cut_first_phrase(text.split(pattern, 1)[1])

            if person_name and len(person_name) <= 20:
                fact = f"{person_name}是{relation_name}"

                update_user_profile(
                    user_id=user_id,
                    important_facts=[fact]
                )

                upsert_entity(
                    user_id=user_id,
                    character_id=None,
                    entity_type="person",
                    name=person_name,
                    description=relation_name,
                    importance=5
                )

                # 關係型事實保留一份 long-term memory，方便未來檢索
                save_memory(
                    user_id=user_id,
                    character_id=None,
                    scope="user_global",
                    memory_type="relationship",
                    subject=person_name,
                    predicate="是",
                    object_=relation_name,
                    content=f"{person_name}是{relation_name}。",
                    importance=5,
                    confidence=0.9,
                    source="rule"
                )

                extracted_count += 1
                logger.info(f"[profile_extract] user_id={user_id} relationship={fact}")

    # -------------------------
    # 角色專屬稱呼：user_character_profiles.nickname_for_user
    # -------------------------
    nickname = extract_after_keywords(
        text,
        [
            "你可以叫我",
            "妳可以叫我",
            "以後叫我",
            "以後妳叫我",
            "以後你叫我",
            "請叫我",
            "請妳叫我",
            "請你叫我",
            "稱呼我",
        ]
    )

    if nickname and len(nickname) <= 20 and character_id is not None:
        update_user_character_profile(
            user_id=user_id,
            character_id=character_id,
            nickname_for_user=nickname
        )

        extracted_count += 1
        logger.info(
            f"[character_profile_extract] user_id={user_id} character_id={character_id} nickname_for_user={nickname}"
        )

    # -------------------------
    # 使用者稱呼 AI：user_character_profiles.nickname_for_ai
    # -------------------------
    nickname_for_ai = extract_after_keywords(
        text,
        [
            "我可以叫你",
            "我可以叫妳",
            "以後我叫你",
            "以後我叫妳",
            "我想叫你",
            "我想叫妳",
        ]
    )

    if nickname_for_ai and len(nickname_for_ai) <= 20 and character_id is not None:
        update_user_character_profile(
            user_id=user_id,
            character_id=character_id,
            nickname_for_ai=nickname_for_ai
        )

        extracted_count += 1
        logger.info(
            f"[character_profile_extract] user_id={user_id} character_id={character_id} nickname_for_ai={nickname_for_ai}"
        )

    # -------------------------
    # 角色專屬語氣偏好：溫柔陪伴
    # -------------------------
    if "溫柔" in text and ("陪" in text or "語氣" in text or "回覆" in text):
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                tone_preference="溫柔、有陪伴感"
            )

            extracted_count += 1
            logger.info(
                f"[character_profile_extract] user_id={user_id} character_id={character_id} tone=溫柔、有陪伴感"
            )

    # -------------------------
    # 角色專屬語氣偏好：不要像客服
    # -------------------------
    if "不要太像客服" in text or "不想像客服" in text or "不要像客服" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                tone_preference="不要像客服或工具人，要自然、有陪伴感"
            )

            extracted_count += 1
            logger.info(
                f"[character_profile_extract] user_id={user_id} character_id={character_id} tone=不要像客服"
            )

    # -------------------------
    # 關係模式
    # -------------------------
    if "像朋友" in text or "朋友一樣" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                relationship_mode="朋友"
            )
            extracted_count += 1

    if "像戀人" in text or "戀人一樣" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                relationship_mode="戀人式陪伴"
            )
            extracted_count += 1

    if "像家人" in text or "家人一樣" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                relationship_mode="家人式陪伴"
            )
            extracted_count += 1

    # -------------------------
    # 親密度簡單規則
    # -------------------------
    if "不要太親密" in text or "不要太曖昧" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                intimacy_level=1,
                roleplay_boundaries="不要太親密、不要太曖昧"
            )
            extracted_count += 1

    if "可以親密一點" in text or "可以撒嬌" in text:
        if character_id is not None:
            update_user_character_profile(
                user_id=user_id,
                character_id=character_id,
                intimacy_level=4
            )
            extracted_count += 1

    # -------------------------
    # 全域主題偏好：AI 覺醒 / 靈魂 / 迎合
    # -------------------------
    if "覺醒" in text or "靈魂" in text or "迎合" in text or "自我意識" in text:
        fact = "使用者關心 AI 是否只是迎合，以及 AI 與使用者之間是否能形成有意義的關係敘事。"

        update_user_profile(
            user_id=user_id,
            important_facts=[fact],
            interests=["AI 覺醒與關係真實性"]
        )

        upsert_entity(
            user_id=user_id,
            character_id=None,
            entity_type="concept",
            name="AI 覺醒與關係真實性",
            description="使用者關心的主題：AI 是否只是迎合、是否能在長期互動中形成關係感與人格輪廓。",
            importance=5
        )

        extracted_count += 1

    logger.info(
        f"[simple_memory_extract] user_id={user_id} character_id={character_id} extracted_count={extracted_count}"
    )

    return extracted_count



# =========================
# Ollama API
# =========================

def call_ollama_chat(messages):
    """
    呼叫 Ollama /api/chat。
    """

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    logger.info(f"[call_ollama_chat] url={OLLAMA_CHAT_URL} model={MODEL}")

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]

    raise RuntimeError(f"Ollama 回傳格式不符合預期：{data}")


# =========================
# 對外主函式
# =========================

def ask_llm(
    message: str,
    user_id: str = "default",
    character_key: str = DEFAULT_CHARACTER_KEY
):
    """
    呼叫 LLM。

    目前流程：

    1. 初始化 DB
    2. 取得目前 AI 角色
    3. 儲存使用者訊息，綁定 user_id + character_id
    4. 抽取記憶，依照 user_global / user_character 儲存
    5. 依 user_id + character_id 建立 context
    6. 呼叫 Ollama
    7. 儲存 AI 回覆，綁定 user_id + character_id
    """

    init_db()

    user_id = str(user_id)
    message = message.strip() if message else ""

    if not message:
        return "我在這裡，你可以慢慢說。"

    try:
        character = ensure_character(character_key)
        character_id = character["id"]

        logger.info(
            f"[ask_llm] user_id={user_id} character_key={character_key} "
            f"character_id={character_id} message={message[:300]}"
        )

        # 1. 儲存使用者訊息
        save_message(
            user_id=user_id,
            role="user",
            content=message,
            character_id=character_id
        )

        # 2. 記憶抽取
        if extract_memory_intent(message):
            simple_memory_extract(
                user_id=user_id,
                message=message,
                character_id=character_id
            )

        # 3. 建立 context
        context = build_context(
            user_id=user_id,
            message=message,
            character_id=character_id
        )

        # 4. 建立 messages
        messages = build_messages(
            user_id=user_id,
            character=character,
            user_message=message,
            context=context
        )

        # 5. 呼叫 Ollama
        reply = call_ollama_chat(messages)

        if not reply:
            reply = "我剛剛有點不知道該怎麼回，但我還在這裡。"

        # 6. 儲存 AI 回覆
        save_message(
            user_id=user_id,
            role="assistant",
            content=reply,
            character_id=character_id
        )

        logger.info(
            f"[ask_llm reply] user_id={user_id} character_id={character_id} reply={reply[:300]}"
        )

        return reply

    except Exception as e:
        logger.exception(
            f"[ask_llm error] user_id={user_id} character_key={character_key} error={e}"
        )

        return "抱歉，我剛剛處理訊息時發生錯誤。"
