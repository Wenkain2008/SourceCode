import sqlite3
import json
import numpy as np
from .llm import chat, get_embedding



# Initialize the database and create the messages table if it doesn't exist

def init_db():
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT CHECK(role IN ('system', 'user', 'assistant', 'tool')),
            content TEXT,
            embedding TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# method to save messages to the database

def save_message(session_id, role, content):
    if not isinstance(content, str):
        content = json.dumps(content)

    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    content_vector = get_embedding(content)
    embedding_json = json.dumps(content_vector)
    cursor.execute(
        "INSERT INTO messages (session_id, role, content, embedding) VALUES (?, ?, ?, ?)",
        (session_id, role, content, embedding_json)
    )
    conn.commit()
    conn.close()

def save_memory(content):
    embedding = get_embedding(content)
    embedding_json = json.dumps(embedding)

    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (content, embedding) VALUES (?, ?)",
        (content, embedding_json)
    )
    conn.commit()
    conn.close()



# method to retrieve all messages from the database

def get_all_messages():
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    rows = cursor.fetchall()
    conn.close()
    return rows


def cosine_similarity(vec_a, vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_similar(query, table="messages", top_n=3):
    query_vector = get_embedding(query)

    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, content, embedding FROM {table} WHERE embedding IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    scored = []
    for row_id, content, embedding_json in rows:
        stored_vector = json.loads(embedding_json)
        similarity = cosine_similarity(query_vector, stored_vector)
        scored.append((similarity, row_id, content))

    scored.sort(reverse=True)
    top_results = scored[:top_n]
    return top_results



def extract_memory_chunks(conversation_messages, model):
    conversation_only = [m for m in conversation_messages if m["role"] != "system"]

    conversation_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in conversation_only
    )

    extraction_request = {
    "role": "user",
    "content": (
        f"Here is a conversation:\n{conversation_text}\n\n"
        "List important facts about the user as a JSON array of strings. "
        "Each fact must be a complete sentence, for example: \"The user's name is Yannik.\" "
        "Do not just write a single word or name by itself. "
        "Only real information, no greetings or small talk. "
        "Respond with ONLY the JSON array."
    )
}

    response = chat([extraction_request], model=model)
    raw_text = response["message"]["content"]

    start = raw_text.find("[")
    end = raw_text.rfind("]")

    print("DEBUG raw extraction output:", raw_text)   # add back temporarily, before the try/except
    try:
        chunks = json.loads(raw_text[start:end+1])
    except (json.JSONDecodeError, ValueError):
        return []

    valid_chunks = [c for c in chunks if isinstance(c, str) and " " in c]
    return valid_chunks


def process_memory_chunk(chunk, model):
    results = search_similar(chunk, table="memories", top_n=1)

    if not results:
        print(f"DEBUG: '{chunk}' -> no existing memories, saving as new")
        save_memory(chunk)
        return

    best_score, best_id, best_content = results[0]
    print(f"DEBUG: '{chunk}' -> best match (score={best_score:.3f}): '{best_content}'")

    if best_score < 0.5:
        print("DEBUG: below threshold -> saving as new")
        save_memory(chunk)
    elif best_score > 0.92:
        print("DEBUG: above threshold -> treating as duplicate, skipping")
    else:
        action = judge_memory_update(chunk, best_content, model)
        print(f"DEBUG: ambiguous zone -> LLM judged action = '{action}'")
        if action == "new":
            save_memory(chunk)
        elif action == "update":
            update_memory(best_id, chunk)
    


def update_memory(memory_id, new_content):
    embedding = get_embedding(new_content)
    embedding_json = json.dumps(embedding)
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memories SET content = ?, embedding = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_content, embedding_json, memory_id)
    )
    conn.commit()
    conn.close()




def judge_memory_update(new_chunk, existing_memory, model):
    judge_prompt = {
        "role": "system",
        "content": (
            "You compare two pieces of information about a user. "
            "EXISTING MEMORY: " + existing_memory + "\n"
            "NEW INFORMATION: " + new_chunk + "\n\n"
            "Decide one of three actions:\n"
            "- \"duplicate\": new information says essentially the same thing as the existing memory\n"
            "- \"update\": new information refines, corrects, or extends the existing memory\n"
            "- \"new\": new information is genuinely distinct and unrelated enough to keep both\n\n"
            "Respond with ONLY a raw JSON object, nothing else, in this exact format: "
            '{"action": "duplicate"} or {"action": "update"} or {"action": "new"}'
        )
    }

    response = chat([judge_prompt], model=model)
    raw_text = response["message"]["content"]

    start = raw_text.find("{")
    end = raw_text.rfind("}")


    try:
        result = json.loads(raw_text[start:end+1])
        action = result.get("action", "new")
    except (json.JSONDecodeError, ValueError):
        action = "new"

    return action


if __name__ == "__main__":
    init_db()