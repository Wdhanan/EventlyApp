import os
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from datetime import datetime
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# Router für Chat-Endpunkte
chat_router = APIRouter(prefix="/chat", tags=["chat"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../data/eventmanager.db")

# CORS Einstellungen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ChatMessage(BaseModel):
    user_id: int
    event_id: Optional[int] = None
    task_id: Optional[int] = None
    role: str  # 'user' oder 'assistant'
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    id: int
    user_id: int
    event_id: Optional[int]
    task_id: Optional[int]
    role: str
    content: str
    timestamp: str


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Chat-Historie abrufen
@chat_router.get("/history")
def get_chat_history(
    user_id: int,
    event_id: Optional[int] = None,
    task_id: Optional[int] = None
):
    """
    Lädt die Chat-Historie für einen Benutzer, Event und/oder Task.
    """
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Datenbankverbindung fehlgeschlagen")
    
    try:
        cursor = conn.cursor()
        
        # SQL-Query basierend auf verfügbaren Parametern
        if task_id:
            # Spezifische Task-Chat-Historie
            query = """
                SELECT id, user_id, event_id, task_id, role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ? AND task_id = ?
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (user_id, task_id))
        elif event_id:
            # Event-Chat-Historie (ohne spezifische Task)
            query = """
                SELECT id, user_id, event_id, task_id, role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ? AND event_id = ? AND task_id IS NULL
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (user_id, event_id))
        else:
            # Allgemeine Chat-Historie des Benutzers
            query = """
                SELECT id, user_id, event_id, task_id, role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ?
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (user_id,))
        
        rows = cursor.fetchall()
        
        # Ergebnisse in Dictionary-Format umwandeln
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "user_id": row[1],
                "event_id": row[2],
                "task_id": row[3],
                "role": row[4],
                "content": row[5],
                "timestamp": row[6]
            })
        
        return history
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
    finally:
        conn.close()

# Chat-Nachricht senden/speichern
@chat_router.post("/send")
def send_chat_message(message: ChatMessage):
    """
    Speichert eine Chat-Nachricht in der Datenbank.
    """
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Datenbankverbindung fehlgeschlagen")
    
    try:
        cursor = conn.cursor()
        
        # Nachricht in Datenbank einfügen
        cursor.execute("""
            INSERT INTO chat_messages (user_id, event_id, task_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.user_id,
            message.event_id,
            message.task_id,
            message.role,
            message.content,
            message.timestamp
        ))
        
        conn.commit()
        message_id = cursor.lastrowid
        
        return {
            "status": "success",
            "message": "Nachricht erfolgreich gespeichert",
            "message_id": message_id
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
    finally:
        conn.close()

# Chat-Historie löschen
@chat_router.delete("/clear")
def clear_chat_history(
    user_id: int,
    event_id: Optional[int] = None,
    task_id: Optional[int] = None
):
    """
    Löscht die Chat-Historie für einen Benutzer, Event und/oder Task.
    """
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Datenbankverbindung fehlgeschlagen")
    
    try:
        cursor = conn.cursor()
        
        if task_id:
            # Spezifische Task-Chat löschen
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE user_id = ? AND task_id = ?
            """, (user_id, task_id))
        elif event_id:
            # Event-Chat löschen
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE user_id = ? AND event_id = ?
            """, (user_id, event_id))
        else:
            # Alle Chats des Benutzers löschen
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE user_id = ?
            """, (user_id,))
        
        conn.commit()
        deleted_count = cursor.rowcount
        
        return {
            "status": "success",
            "message": f"{deleted_count} Nachrichten gelöscht"
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
    finally:
        conn.close()

# Statistiken für Chat-Aktivität
@chat_router.get("/stats")
def get_chat_stats(user_id: int, event_id: Optional[int] = None):
    """
    Gibt Statistiken über Chat-Aktivität zurück.
    """
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Datenbankverbindung fehlgeschlagen")
    
    try:
        cursor = conn.cursor()
        
        if event_id:
            # Event-spezifische Statistiken
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as ai_messages,
                    MIN(timestamp) as first_message,
                    MAX(timestamp) as last_message
                FROM chat_messages 
                WHERE user_id = ? AND event_id = ?
            """, (user_id, event_id))
        else:
            # Allgemeine Benutzer-Statistiken
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as ai_messages,
                    MIN(timestamp) as first_message,
                    MAX(timestamp) as last_message
                FROM chat_messages 
                WHERE user_id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                "total_messages": result[0],
                "user_messages": result[1],
                "ai_messages": result[2],
                "first_message": result[3],
                "last_message": result[4]
            }
        else:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "ai_messages": 0,
                "first_message": None,
                "last_message": None
            }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
    finally:
        conn.close()

# Hilfsfunktion für die Streamlit-App
def get_chat_history_for_streamlit(user_id, event_id=None, task_id=None):
    """
    Direkte Datenbankabfrage für Streamlit (Fallback ohne API-Call).
    """
    conn = get_db()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        if task_id:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ? AND task_id = ?
                ORDER BY timestamp ASC
            """, (user_id, task_id))
        elif event_id:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ? AND event_id = ? AND task_id IS NULL
                ORDER BY timestamp ASC
            """, (user_id, event_id))
        else:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM chat_messages 
                WHERE user_id = ?
                ORDER BY timestamp ASC
            """, (user_id,))
        
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "role": row[0],
                "content": row[1],
                "timestamp": row[2]
            })
        
        return history
        
    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
        return []
    finally:
        conn.close()

def save_chat_message_direct(user_id, event_id, task_id, role, content, timestamp):
    """
    Direkte Speicherung von Chat-Nachrichten ohne API-Call.
    """
    conn = get_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (user_id, event_id, task_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, event_id, task_id, role, content, timestamp))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Fehler beim Speichern der Nachricht: {e}")
        return False
    finally:
     
        conn.close()


app.include_router(chat_router)


