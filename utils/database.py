import sqlite3
from sqlite3 import Error

def create_connection():
    """Erstelle eine Verbindung zur SQLite-Datenbank."""
    conn = None
    try:
        conn = sqlite3.connect("data/eventmanager.db")  
        return conn
    except Error as e:
        print(e)
    return conn

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
            # Tabelle für Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
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
            # Tabelle für Statistiken
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                task_id INTEGER,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (event_id) REFERENCES events (id)
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
            conn.commit()
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



if __name__ == "__main__":
    create_tables()
    
