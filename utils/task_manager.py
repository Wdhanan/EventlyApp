import streamlit as st
import sqlite3
from sqlite3 import Error
from utils.database import create_connection

def save_task(event_id, title, content):
    """
    Speichert eine neue Aufgabe (Task) in der Datenbank.
    :param event_id: Die ID des Events, zu dem die Aufgabe gehört
    :param title: Der Titel der Aufgabe
    :param content: Der Inhalt der Aufgabe
    """
    if title and content:
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (event_id, title, content) VALUES (?, ?, ?)",
                    (event_id, title, content),
                )
                conn.commit()
                st.success("Aufgabe gespeichert!")
            except Error as e:
                st.error(f"Fehler beim Speichern der Aufgabe: {e}")
            finally:
                conn.close()
    else:
        st.error("Titel und Inhalt dürfen nicht leer sein.")

def edit_task(task_id, new_title, new_content):
    """
    Bearbeitet eine vorhandene Aufgabe.
    :param task_id: Die ID der Aufgabe
    :param new_title: Der neue Titel der Aufgabe
    :param new_content: Der neue Inhalt der Aufgabe
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET title = ?, content = ? WHERE id = ?",
                (new_title, new_content, task_id),
            )
            conn.commit()
            st.success("Aufgabe erfolgreich bearbeitet!")
        except Error as e:
            st.error(f"Fehler beim Bearbeiten der Aufgabe: {e}")
        finally:
            conn.close()

def share_task(task_id, shared_by_user_id, shared_with_username):
    """
    Teilt eine Aufgabe mit einem anderen Benutzer.
    :param task_id: Die ID der Aufgabe
    :param shared_by_user_id: Die ID des Benutzers, der die Aufgabe teilt
    :param shared_with_username: Der Benutzername des Empfängers
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Hole die Benutzer-ID des Empfängers basierend auf dem Benutzernamen
            cursor.execute("SELECT id FROM users WHERE username = ?", (shared_with_username,))
            shared_with_user = cursor.fetchone()
            if shared_with_user:
                shared_with_user_id = shared_with_user[0]
                # Füge die geteilte Aufgabe in die Datenbank ein
                cursor.execute(
                    "INSERT INTO shared_tasks (task_id, shared_by_user_id, shared_with_user_id) VALUES (?, ?, ?)",
                    (task_id, shared_by_user_id, shared_with_user_id),
                )
                conn.commit()
                st.success(f"Aufgabe erfolgreich mit {shared_with_username} geteilt!")
            else:
                st.error(f"Benutzer '{shared_with_username}' nicht gefunden.")
        except Error as e:
            st.error(f"Fehler beim Teilen der Aufgabe: {e}")
        finally:
            conn.close()

def load_shared_tasks(user_id):
    """
    Lädt die mit dem Benutzer geteilten Aufgaben.
    :param user_id: Die ID des Benutzers
    :return: Liste der geteilten Aufgaben
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tasks.id, tasks.title, tasks.content, users.username
                FROM shared_tasks
                JOIN tasks ON shared_tasks.task_id = tasks.id
                JOIN users ON shared_tasks.shared_by_user_id = users.id
                WHERE shared_tasks.shared_with_user_id = ?
            """, (user_id,))
            shared_tasks = cursor.fetchall()
            return shared_tasks
        except Error as e:
            st.error(f"Fehler beim Laden der geteilten Aufgaben: {e}")
        finally:
            conn.close()
    return []

def load_tasks(event_id):
    """
    Lädt alle Aufgaben für ein bestimmtes Event.
    :param event_id: Die ID des Events
    :return: Liste der Aufgaben
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content FROM tasks WHERE event_id = ?", (event_id,))
            tasks = cursor.fetchall()
            return tasks
        except Error as e:
            st.error(f"Fehler beim Laden der Aufgaben: {e}")
        finally:
            conn.close()
    return []

def delete_task(task_id):
    """
    Löscht eine Aufgabe aus der Datenbank.
    :param task_id: Die ID der Aufgabe
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            st.success("Aufgabe gelöscht!")
        except Error as e:
            st.error(f"Fehler beim Löschen der Aufgabe: {e}")
        finally:
            conn.close()
            