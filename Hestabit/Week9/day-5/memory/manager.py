import sqlite3
import os
from datetime import datetime
from memory.session_memory import SessionMemory
from memory.vector_store import VectorStore
from llm.router import generate

DB_PATH = "memory/long_term.db"

class MemoryManager:
    def __init__(self):
        self.session = SessionMemory()
        self.vector_store = VectorStore()
        self._init_db()

    def _init_db(self):
        os.makedirs("memory", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def store_interaction(self, role, content):
        """Conversation stored in both session and SQLite."""
        # 1. Session Memory
        self.session.add_message(role, content)
        
        # 2. Long-term SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()

    def get_augmented_context(self, query):
        """Search memory -> Fetch similar context."""
        relevant_facts = self.vector_store.search(query, top_k=2)
        if not relevant_facts:
            return ""
        
        context = "\n### RECALLED MEMORY\n"
        for fact in relevant_facts:
            context += f"- {fact}\n"
        return context

    def summarize_and_store_fact(self):
        """Important facts summarized and stored in FAISS."""
        history_text = self.session.get_full_text()
        if not history_text:
            return
            
        summary_prompt = f"""Summarize the following conversation into 1-2 key facts that are worth remembering for the long term. 
If there's nothing important, reply with 'NONE'.

Conversation:
{history_text}

Summary fact:"""
        
        try:
            summary = generate("You are a memory compressor.", summary_prompt)
            if summary and summary.strip().upper() != "NONE":
                self.vector_store.add_fact(summary.strip())
                print(f"  [MEMORY] New fact stored: {summary.strip()}")
        except Exception as e:
            print(f"  [MEMORY WARN] Failed to summarize: {e}")

if __name__ == "__main__":
    mm = MemoryManager()
    mm.store_interaction("user", "My name is Abhay.")
    mm.summarize_and_store_fact()
    print("Augmented Context for 'who am I?':", mm.get_augmented_context("who am I?"))
