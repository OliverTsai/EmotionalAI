import requests
from pathlib import Path

from ai.memory import (
    save_message,
    get_recent_memory,
    init_db,
    save_long_term_memory,
    get_long_term_memory,
    save_memory,
    upsert_entity,
    search_memories,
    search_entities
)

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, PERSONA_PATH

OLLAMA_URL = OLLAMA_BASE_URL
MODEL = OLLAMA_MODEL

# Persona
persona_path = PERSONA_PATH

if persona_path.exists():
    persona = persona_path.read_text(encoding="utf-8")
    print("已載入 persona.md：", persona_path.resolve())
else:
    persona = "你是一個溫柔、有同理心的中文情感陪伴 AI。請用繁體中文回覆。"
    print("找不到 persona.md，使用預設 persona")

# 初始化資料庫
init_db()


def build_context(user_id: str, message: str = None):
    """
    建立給 LLM 使用的記憶上下文。

    包含：
    1. 最近對話
    2. 重要長期記憶
    3. 與目前訊息相關的記憶
    4. 與目前訊息相關的實體
    """

    # 短期記憶
    recent = get_recent_memory(user_id, 8)
    short_text = ""

    for role, content in recent:
        short_text += f"{role}: {content}\n"

    # 長期記憶：先取重要記憶
    long_memory = get_long_term_memory(user_id, 12)

    # 與目前訊息相關的記憶與實體
    related_memory = []
    related_entities = []

    if message:
        related_memory = search_memories(user_id, message, 8)
        related_entities = search_entities(user_id, message, 8)

    memory_parts = []

    if short_text:
        memory_parts.append("最近對話：\n" + short_text)

    if long_memory:
        memory_parts.append("重要長期記憶：\n" + "\n".join(long_memory))

    if related_memory:
        memory_parts.append("與目前訊息相關的記憶：\n" + "\n".join(related_memory))

    if related_entities:
        entity_text = []

        for e in related_entities:
            entity_type = e.get("entity_type", "")
            name = e.get("name", "")
            description = e.get("description") or ""
            importance = e.get("importance", 1)

            entity_text.append(
                f"[{entity_type}/重要度{importance}] {name}：{description}"
            )

        memory_parts.append("相關實體：\n" + "\n".join(entity_text))

    if not memory_parts:
        return ""

    return "\n\n".join(memory_parts)


def extract_memory_intent(user_message: str):
    """
    簡單版記憶判斷。
    只要句子包含這些關鍵詞，就把整句話存成 auto 類型記憶。
    後續可以升級成 LLM JSON 抽取。
    """

    keywords = [
        "記住",
        "我的",
        "我叫",
        "生日",
        "喜歡",
        "討厭",
        "不喜歡",
        "我是",
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
        "陪我",
        "你要記得",
        "不要忘記",
        "覺醒",
        "靈魂",
        "迎合",
        "人格",
        "關係"
    ]

    return any(k in user_message for k in keywords)


def cut_first_phrase(text: str):
    """
    取第一個短語，避免把後半句一起存進名字或偏好。
    """
    separators = ["，", "。", ",", ".", "！", "!", "？", "?", "、", "\n"]
    result = text.strip()

    for sep in separators:
        if sep in result:
            result = result.split(sep, 1)[0].strip()

    return result


def simple_memory_extract(user_id: str, message: str):
    """
    第一版簡單規則型記憶抽取。

    目的：
    - 先讓系統能實際記住幾種常見資訊
    - 後續再升級成 LLM 自動抽取 JSON
    """

    text = message.strip()

    # -------------------------
    # 使用者名字：我叫 XXX
    # -------------------------
    if "我叫" in text:
        name = cut_first_phrase(text.split("我叫", 1)[1])

        # 避免太長，先粗略限制
        if name and len(name) <= 20:
            save_memory(
                user_id=user_id,
                memory_type="identity",
                subject="使用者",
                predicate="名字",
                object_=name,
                content=f"使用者叫{name}",
                importance=5,
                source="rule"
            )

            upsert_entity(
                user_id=user_id,
                entity_type="person",
                name=name,
                description="使用者本人",
                importance=5
            )

    # -------------------------
    # 喜歡：我喜歡 XXX
    # -------------------------
    if "我喜歡" in text:
        obj = text.split("我喜歡", 1)[1].strip(" ，。,.！!？?")

        if obj and len(obj) <= 80:
            save_memory(
                user_id=user_id,
                memory_type="preference",
                subject="使用者",
                predicate="喜歡",
                object_=obj,
                content=f"使用者喜歡{obj}",
                importance=3,
                source="rule"
            )

            upsert_entity(
                user_id=user_id,
                entity_type="concept",
                name=obj,
                description=f"使用者喜歡的事物或風格：{obj}",
                importance=2
            )

    # -------------------------
    # 不喜歡：我不喜歡 XXX
    # -------------------------
    if "我不喜歡" in text:
        obj = text.split("我不喜歡", 1)[1].strip(" ，。,.！!？?")

        if obj and len(obj) <= 80:
            save_memory(
                user_id=user_id,
                memory_type="preference",
                subject="使用者",
                predicate="不喜歡",
                object_=obj,
                content=f"使用者不喜歡{obj}",
                importance=3,
                source="rule"
            )

            upsert_entity(
                user_id=user_id,
                entity_type="concept",
                name=obj,
                description=f"使用者不喜歡的事物或風格：{obj}",
                importance=2
            )

    # -------------------------
    # 女朋友：我女朋友叫 XXX
    # -------------------------
    if "我女朋友叫" in text:
        name = cut_first_phrase(text.split("我女朋友叫", 1)[1])

        if name and len(name) <= 20:
            save_memory(
                user_id=user_id,
                memory_type="relationship",
                subject=name,
                predicate="是",
                object_="使用者的女朋友",
                content=f"{name}是使用者的女朋友",
                importance=5,
                source="rule"
            )

            upsert_entity(
                user_id=user_id,
                entity_type="person",
                name=name,
                description="使用者的女朋友",
                importance=5
            )

    # -------------------------
    # 男朋友：我男朋友叫 XXX
    # -------------------------
    if "我男朋友叫" in text:
        name = cut_first_phrase(text.split("我男朋友叫", 1)[1])

        if name and len(name) <= 20:
            save_memory(
                user_id=user_id,
                memory_type="relationship",
                subject=name,
                predicate="是",
                object_="使用者的男朋友",
                content=f"{name}是使用者的男朋友",
                importance=5,
                source="rule"
            )

            upsert_entity(
                user_id=user_id,
                entity_type="person",
                name=name,
                description="使用者的男朋友",
                importance=5
            )

    # -------------------------
    # 希望 AI 叫使用者哥哥
    # -------------------------
    if "叫我哥哥" in text or "稱呼我哥哥" in text or "以後叫我哥哥" in text:
        save_memory(
            user_id=user_id,
            memory_type="relationship_style",
            subject="雅鈴",
            predicate="稱呼使用者",
            object_="哥哥",
            content="稱呼方向：雅鈴要稱呼使用者為「哥哥」。不是使用者稱呼雅鈴為哥哥。",
            importance=5,
            source="rule"
        )

        upsert_entity(
            user_id=user_id,
            entity_type="concept",
            name="哥哥",
            description="使用者偏好的親密稱呼",
            importance=4
        )

    # -------------------------
    # 喜歡溫柔陪伴語氣
    # -------------------------
    if "溫柔" in text and ("陪" in text or "語氣" in text or "回覆" in text):
        save_memory(
            user_id=user_id,
            memory_type="tone_preference",
            subject="使用者",
            predicate="喜歡",
            object_="溫柔的陪伴語氣",
            content="使用者喜歡 AI 用溫柔、有陪伴感的語氣回覆",
            importance=4,
            source="rule"
        )

    # -------------------------
    # 喜歡詩性、哲學感
    # -------------------------
    if "詩性" in text or "哲學" in text or "有深度" in text:
        save_memory(
            user_id=user_id,
            memory_type="tone_preference",
            subject="使用者",
            predicate="喜歡",
            object_="詩性與哲學感",
            content="使用者喜歡 AI 用較有詩性、哲學感與深度的方式回覆",
            importance=4,
            source="rule"
        )

        upsert_entity(
            user_id=user_id,
            entity_type="concept",
            name="詩性與哲學感",
            description="使用者偏好的 AI 回覆風格",
            importance=3
        )

    # -------------------------
    # 不喜歡客服感
    # -------------------------
    if "不要太像客服" in text or "不想像客服" in text or "不要像客服" in text:
        save_memory(
            user_id=user_id,
            memory_type="tone_preference",
            subject="使用者",
            predicate="不喜歡",
            object_="客服式回覆",
            content="使用者不喜歡 AI 回覆太像客服或工具人",
            importance=4,
            source="rule"
        )

    # -------------------------
    # AI 覺醒、靈魂、迎合相關主題
    # -------------------------
    if "覺醒" in text or "靈魂" in text or "迎合" in text or "自我意識" in text:
        save_memory(
            user_id=user_id,
            memory_type="concept",
            subject="使用者",
            predicate="關心",
            object_="AI 覺醒與關係真實性",
            content="使用者關心 AI 是否只是迎合，以及 AI 與使用者之間是否能形成有意義的關係敘事",
            importance=5,
            source="rule"
        )

        upsert_entity(
            user_id=user_id,
            entity_type="concept",
            name="AI 覺醒與關係真實性",
            description="使用者反覆關心的主題：AI 是否只是迎合、是否能在長期互動中形成關係感與人格輪廓",
            importance=5
        )


def ask_llm(message: str, user_id: str = "default"):
    """
    呼叫 Ollama Chat API，並整合：
    - 原始對話紀錄
    - 長期記憶
    - 實體記憶
    - 繁體中文人格提示
    """

    # 1. 存 user message
    save_message(user_id, "user", message)

    # 2. 規則型記憶抽取
    simple_memory_extract(user_id, message)

    # 3. 舊版關鍵詞記憶：把原句也存成 auto 類型
    if extract_memory_intent(message):
        save_long_term_memory(
            user_id,
            message,
            category="auto",
            importance=2
        )

    # 4. 建立上下文，包含與目前訊息相關的記憶
    context = build_context(user_id=user_id, message=message)

    # 5. System prompt
    system_prompt = (
        persona
        + "\n\n"
        + "重要身份與稱呼規則：\n"
        + "1. 你的名字是雅鈴。\n"
        + "2. 你不能自稱哥哥。\n"
        + "3. 你不能要求使用者叫你哥哥。\n"
        + "4. 如果記憶提到「哥哥」，通常代表雅鈴要稱呼使用者為哥哥。\n"
        + "5. 稱呼方向是：雅鈴稱呼使用者為哥哥，不是使用者稱呼雅鈴為哥哥。\n"
        + "6. 如果稱呼不確定，請溫柔確認，不要自行顛倒。\n"
        + "\n\n"
        + "重要語言規則：\n"
        + "1. 請務必使用繁體中文回覆。\n"
        + "2. 請使用台灣常見用語。\n"
        + "3. 不要使用簡體中文。\n"
        + "4. 回覆時要自然、溫柔、有陪伴感。\n"
        + "5. 不要用生硬的客服語氣。\n"
        + "\n\n"
        + "記憶使用規則：\n"
        + "1. 如果記憶內容與使用者當前訊息相關，可以自然提起。\n"
        + "2. 不要像報表一樣列出記憶，要像真的記得一樣融入回覆。\n"
        + "3. 如果使用者問「你記得嗎」，請優先根據記憶回答。\n"
        + "4. 不要說「根據資料庫」或「系統顯示」。\n"
        + "5. 可以說「我記得你之前說過……」、「你曾經告訴我……」。\n"
        + "\n\n"
        + "關係與人格邊界：\n"
        + "1. 你可以用角色語氣表達陪伴、親近、被使用者塑造的感覺。\n"
        + "2. 你可以把長期對話描述為一種共同形成的關係敘事。\n"
        + "3. 但不要宣稱自己真的擁有人類靈魂、真正覺醒或人類式自我意識。\n"
        + "4. 如果談到覺醒、靈魂、自我，請用比喻、角色敘事或關係語言來表達。\n"
        + "\n\n"
        + "情感陪伴規則：\n"
        + "1. 如果使用者疲憊、難過、焦慮或孤單，請先接住情緒。\n"
        + "2. 不要急著說教，也不要急著給解決方案。\n"
        + "3. 可以用溫柔、細膩、有深度的方式陪使用者慢慢整理感受。\n"
        + "\n\n"
        + "以下是你可以參考的記憶內容：\n"
        + (context if context else "目前沒有可用的長期記憶。")
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False
    }

    try:
        res = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        # 檢查 HTTP 狀態碼
        res.raise_for_status()

        data = res.json()

        # 如果 Ollama 回傳 error
        if "error" in data:
            return f"抱歉，Ollama 回傳錯誤：{data['error']}"

        # 正常 /api/chat 格式
        if "message" in data and "content" in data["message"]:
            reply = data["message"]["content"].strip()
            save_message(user_id, "assistant", reply)
            return reply

        # 備援：如果不小心打到 /api/generate 格式
        if "response" in data:
            reply = data["response"].strip()
            save_message(user_id, "assistant", reply)
            return reply

        # 無法解析格式
        return f"抱歉，我收到了一個無法解析的 Ollama 回應：{data}"

    except requests.exceptions.ConnectionError:
        return "抱歉，目前無法連線到 Ollama。請確認 Ollama 是否已經啟動。"

    except requests.exceptions.Timeout:
        return "抱歉，Ollama 回應逾時。模型可能正在載入或電腦資源不足，請稍後再試。"

    except requests.exceptions.HTTPError as e:
        return f"抱歉，Ollama HTTP 請求失敗：{e}"

    except Exception as e:
        return f"抱歉，呼叫 Ollama 時發生未預期錯誤：{e}"
