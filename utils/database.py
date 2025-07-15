import sqlite3
from sqlite3 import Error
import os

def create_connection():
    """Erstelle eine Verbindung zur SQLite-Datenbank."""
    conn = None
    try:
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/eventmanager.db")  
        return conn
    except Error as e:
        print(e)
    return conn

def add_is_imported_column():
    """Füge die is_imported Spalte zur events Tabelle hinzu."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Prüfe, ob die Spalte bereits existiert
            cursor.execute("PRAGMA table_info(events)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_imported' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN is_imported INTEGER DEFAULT NULL")
                conn.commit()
                print("Spalte 'is_imported' erfolgreich hinzugefügt.")
            else:
                print("Spalte 'is_imported' existiert bereits.")
        except Error as e:
            print(f"Fehler beim Hinzufügen der Spalte: {e}")
        finally:
            conn.close()

def create_tables():
    """Erstelle die notwendigen Tabellen in der Datenbank."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Tabelle für Benutzer
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            # Tabelle für Events (mit is_imported Spalte)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    is_imported INTEGER DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            # Tabelle für Tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    status TEXT DEFAULT 'in Bearbeitung',
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                shared_by_user_id INTEGER NOT NULL,
                shared_with_user_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (shared_by_user_id) REFERENCES users (id),
                FOREIGN KEY (shared_with_user_id) REFERENCES users (id)
            )
        """)

            # Tabelle für geteilte Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    shared_by_user_id INTEGER NOT NULL,
                    shared_with_user_id INTEGER NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events (id),
                    FOREIGN KEY (shared_by_user_id) REFERENCES users (id),
                    FOREIGN KEY (shared_with_user_id) REFERENCES users (id)
                )
            """)
            # Tabelle für Chatnachrichten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER,
                    task_id INTEGER,
                    role TEXT NOT NULL,         -- 'user' oder 'assistant'
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (event_id) REFERENCES events (id),
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Tabelle für Statistiken (mit fehlendem Komma korrigiert)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                task_id INTEGER,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
<<<<<<< HEAD
                FOREIGN KEY (event_id) REFERENCES events (id),
=======
                FOREIGN KEY (event_id) REFERENCES events (id)
>>>>>>> b6e1ea0f4313903e1659d9e4c9b406ec103080b6
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
            conn.commit()
            print("Tabellen erfolgreich erstellt oder existieren bereits.")
            add_is_imported_column()
            add_is_premium_column()
            add_quiz_limit_columns()
        except Error as e:
            print(e)
        finally:
            conn.close()

def get_event_by_id(event_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Fehler beim Abrufen des Events: {e}")
        finally:
            conn.close()
    return None

def get_tasks_by_event_id(event_id):
    conn = create_connection()
    tasks = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE event_id = ?", (event_id,))
            rows = cursor.fetchall()
            for row in rows:
                tasks.append(row)
        except Error as e:
            print(f"Fehler beim Abrufen der Aufgaben: {e}")
        finally:
            conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = create_connection()
    task = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
        except Error as e:
            print(f"Fehler beim Abrufen der Aufgabe: {e}")
        finally:
            conn.close()
    return task

def get_username_by_id(user_id):
    conn = create_connection()
    username = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
        except Error as e:
            print(f"Fehler beim Abrufen des Benutzernamens: {e}")
        finally:
            conn.close()
    return username

<<<<<<< HEAD
def add_is_premium_column():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if "is_premium" not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
                conn.commit()
                print("Spalte 'is_premium' erfolgreich hinzugefügt.")
            else:
                print("Spalte 'is_premium' existiert bereits.")
        except Error as e:
            print(f"Fehler bei DB-Erweiterung: {e}")
        finally:
            conn.close()


def add_quiz_limit_columns():
    """Fügt die Spalten daily_quiz_count und last_quiz_reset zur users Tabelle hinzu."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Prüfe, ob 'daily_quiz_count' existiert
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if "daily_quiz_count" not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN daily_quiz_count INTEGER DEFAULT 0")
                print("Spalte 'daily_quiz_count' erfolgreich hinzugefügt.")
            else:
                print("Spalte 'daily_quiz_count' existiert bereits.")

            # Prüfe, ob 'last_quiz_reset' existiert
            if "last_quiz_reset" not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN last_quiz_reset TEXT") # TEXT für ISO-Format Datum
                print("Spalte 'last_quiz_reset' erfolgreich hinzugefügt.")
            else:
                print("Spalte 'last_quiz_reset' existiert bereits.")
            
            conn.commit()
        except Error as e:
            print(f"Fehler bei DB-Erweiterung (Quiz Limit): {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    create_tables()
=======


if __name__ == "__main__":
    create_tables()
    
>>>>>>> b6e1ea0f4313903e1659d9e4c9b406ec103080b6
