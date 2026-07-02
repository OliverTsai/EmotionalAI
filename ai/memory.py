import json

from db.connection import get_conn, now
from db.schema import init_db

# =========================
# message_logs
# =========================

def save_message(
    user_id, role, content, character_id=None, conversation_id=None
    ):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO message_logs (
        user_id, 
        role, 
        content, 
        character_id, 
        conversation_id, 
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        str(user_id), 
        role, 
        content, 
        character_id, 
        conversation_id, 
        now()
    ))

    conn.commit()
    message_id = cursor.lastrowid
    conn.close()

    return message_id


def get_recent_memory(
    user_id, limit=10, character_id=None, conversation_id=None
    ):
    conn = get_conn()
    cursor = conn.cursor()

    if conversation_id is not None:
        cursor.execute("""
        SELECT role, content
        FROM message_logs
        WHERE user_id = ?
          AND conversation_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (str(user_id), conversation_id, limit))

    elif character_id is not None:
        cursor.execute("""
        SELECT role, content
        FROM message_logs
        WHERE user_id = ?
          AND character_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (str(user_id), character_id, limit))

    else:
        cursor.execute("""
        SELECT role, content
        FROM message_logs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (str(user_id), limit))

    rows = cursor.fetchall()
    conn.close()

    return [(r["role"], r["content"]) for r in reversed(rows)]


# =========================
# memories
# =========================

def save_memory(
    user_id,
    memory_type,
    content,
    subject=None,
    predicate=None,
    object_=None,
    importance=1,
    confidence=1.0,
    source="user",
    character_id=None,
    scope="user_global"
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO memories (
        user_id,
        character_id,
        scope,
        memory_type,
        subject,
        predicate,
        object,
        content,
        importance,
        confidence,
        source,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(user_id),
        character_id,
        scope,
        memory_type,
        subject,
        predicate,
        object_,
        content,
        importance,
        confidence,
        source,
        now(),
        now()
    ))

    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()

    return memory_id


def get_long_term_memory(user_id, limit=20, character_id=None):
    conn = get_conn()
    cursor = conn.cursor()

    if character_id is not None:
        cursor.execute("""
        SELECT id, memory_type, scope, subject, predicate, object, content, importance
        FROM memories
        WHERE user_id = ?
          AND status = 'active'
          AND (
                scope = 'user_global'
                OR (
                    scope = 'user_character'
                    AND character_id = ?
                )
              )
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (str(user_id), character_id, limit))
    else:
        cursor.execute("""
        SELECT id, memory_type, scope, subject, predicate, object, content, importance
        FROM memories
        WHERE user_id = ?
          AND status = 'active'
          AND scope = 'user_global'
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (str(user_id), limit))

    rows = cursor.fetchall()

    ids = [r["id"] for r in rows]
    if ids:
        cursor.executemany("""
        UPDATE memories
        SET access_count = access_count + 1,
            last_accessed_at = ?
        WHERE id = ?
        """, [(now(), i) for i in ids])
        conn.commit()

    conn.close()

    return [format_memory_row(r) for r in rows]


def search_memories(user_id, query, limit=10, character_id=None):
    conn = get_conn()
    cursor = conn.cursor()

    like_query = f"%{query}%"

    if character_id is not None:
        cursor.execute("""
        SELECT id, memory_type, scope, subject, predicate, object, content, importance
        FROM memories
        WHERE user_id = ?
          AND status = 'active'
          AND (
                scope = 'user_global'
                OR (
                    scope = 'user_character'
                    AND character_id = ?
                )
              )
          AND (
            content LIKE ?
            OR subject LIKE ?
            OR predicate LIKE ?
            OR object LIKE ?
          )
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (
            str(user_id),
            character_id,
            like_query,
            like_query,
            like_query,
            like_query,
            limit
        ))
    else:
        cursor.execute("""
        SELECT id, memory_type, scope, subject, predicate, object, content, importance
        FROM memories
        WHERE user_id = ?
          AND status = 'active'
          AND scope = 'user_global'
          AND (
            content LIKE ?
            OR subject LIKE ?
            OR predicate LIKE ?
            OR object LIKE ?
          )
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (
            str(user_id),
            like_query,
            like_query,
            like_query,
            like_query,
            limit
        ))

    rows = cursor.fetchall()

    ids = [r["id"] for r in rows]
    if ids:
        cursor.executemany("""
        UPDATE memories
        SET access_count = access_count + 1,
            last_accessed_at = ?
        WHERE id = ?
        """, [(now(), i) for i in ids])
        conn.commit()

    conn.close()

    return [format_memory_row(r) for r in rows]


def format_memory_row(row):
    memory_type = row["memory_type"]
    scope = row["scope"] if "scope" in row.keys() else "unknown"
    subject = row["subject"]
    predicate = row["predicate"]
    obj = row["object"]
    content = row["content"]
    importance = row["importance"]

    if subject and predicate and obj:
        return f"[{scope}/{memory_type}/重要度{importance}] {subject} {predicate} {obj}。補充：{content}"
    else:
        return f"[{scope}/{memory_type}/重要度{importance}] {content}"


# 舊函式相容：給 ollama_client.py 暫時使用
def save_long_term_memory(
    user_id,
    fact,
    category="general",
    importance=1,
    character_id=None,
    scope="user_global"
):
    return save_memory(
        user_id=user_id,
        character_id=character_id,
        scope=scope,
        memory_type=category,
        content=fact,
        subject="使用者",
        predicate="提到",
        object_=fact,
        importance=importance,
        source="user"
    )


# =========================
# entities
# =========================

def upsert_entity(
    user_id,
    entity_type,
    name,
    alias=None,
    description=None,
    attributes=None,
    importance=1,
    character_id=None
):
    conn = get_conn()
    cursor = conn.cursor()

    attributes_json = json.dumps(attributes or {}, ensure_ascii=False)

    cursor.execute("""
    INSERT INTO entities (
        user_id,
        character_id,
        entity_type,
        name,
        alias,
        description,
        attributes_json,
        importance,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, character_id, entity_type, name)
    DO UPDATE SET
        alias = COALESCE(excluded.alias, entities.alias),
        description = COALESCE(excluded.description, entities.description),
        attributes_json = excluded.attributes_json,
        importance = MAX(entities.importance, excluded.importance),
        updated_at = excluded.updated_at
    """, (
        str(user_id),
        character_id,
        entity_type,
        name,
        alias,
        description,
        attributes_json,
        importance,
        now(),
        now()
    ))

    conn.commit()

    cursor.execute("""
    SELECT id FROM entities
    WHERE user_id = ?
      AND character_id IS ?
      AND entity_type = ?
      AND name = ?
    """, (str(user_id), character_id, entity_type, name))

    row = cursor.fetchone()
    conn.close()

    return row["id"] if row else None


def search_entities(user_id, query, limit=10, character_id=None):
    conn = get_conn()
    cursor = conn.cursor()

    like_query = f"%{query}%"

    if character_id is not None:
        cursor.execute("""
        SELECT id, entity_type, name, alias, description, attributes_json, importance
        FROM entities
        WHERE user_id = ?
          AND (
                character_id IS NULL
                OR character_id = ?
              )
          AND (
            name LIKE ?
            OR alias LIKE ?
            OR description LIKE ?
          )
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (
            str(user_id),
            character_id,
            like_query,
            like_query,
            like_query,
            limit
        ))
    else:
        cursor.execute("""
        SELECT id, entity_type, name, alias, description, attributes_json, importance
        FROM entities
        WHERE user_id = ?
          AND character_id IS NULL
          AND (
            name LIKE ?
            OR alias LIKE ?
            OR description LIKE ?
          )
        ORDER BY importance DESC, id DESC
        LIMIT ?
        """, (
            str(user_id),
            like_query,
            like_query,
            like_query,
            limit
        ))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "entity_type": r["entity_type"],
            "name": r["name"],
            "alias": r["alias"],
            "description": r["description"],
            "attributes": json.loads(r["attributes_json"] or "{}"),
            "importance": r["importance"]
        })

    return result


# =========================
# entity_relations
# =========================

def save_entity_relation(
    user_id,
    from_entity_id,
    relation_type,
    to_entity_id,
    description=None,
    importance=1,
    confidence=1.0,
    character_id=None
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO entity_relations (
        user_id,
        character_id,
        from_entity_id,
        relation_type,
        to_entity_id,
        description,
        importance,
        confidence,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(user_id),
        character_id,
        from_entity_id,
        relation_type,
        to_entity_id,
        description,
        importance,
        confidence,
        now(),
        now()
    ))

    conn.commit()
    relation_id = cursor.lastrowid
    conn.close()

    return relation_id


def get_entity_relations(user_id, entity_id, limit=10, character_id=None):
    conn = get_conn()
    cursor = conn.cursor()

    if character_id is not None:
        cursor.execute("""
        SELECT
            r.id,
            r.relation_type,
            r.description,
            r.importance,
            e1.name AS from_name,
            e1.entity_type AS from_type,
            e2.name AS to_name,
            e2.entity_type AS to_type
        FROM entity_relations r
        JOIN entities e1 ON r.from_entity_id = e1.id
        JOIN entities e2 ON r.to_entity_id = e2.id
        WHERE r.user_id = ?
          AND (
                r.character_id IS NULL
                OR r.character_id = ?
              )
          AND (r.from_entity_id = ? OR r.to_entity_id = ?)
        ORDER BY r.importance DESC, r.id DESC
        LIMIT ?
        """, (str(user_id), character_id, entity_id, entity_id, limit))
    else:
        cursor.execute("""
        SELECT
            r.id,
            r.relation_type,
            r.description,
            r.importance,
            e1.name AS from_name,
            e1.entity_type AS from_type,
            e2.name AS to_name,
            e2.entity_type AS to_type
        FROM entity_relations r
        JOIN entities e1 ON r.from_entity_id = e1.id
        JOIN entities e2 ON r.to_entity_id = e2.id
        WHERE r.user_id = ?
          AND r.character_id IS NULL
          AND (r.from_entity_id = ? OR r.to_entity_id = ?)
        ORDER BY r.importance DESC, r.id DESC
        LIMIT ?
        """, (str(user_id), entity_id, entity_id, limit))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(
            f"{r['from_name']} --{r['relation_type']}--> {r['to_name']}。{r['description'] or ''}"
        )

    return result
