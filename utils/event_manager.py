import streamlit as st
import sqlite3
from sqlite3 import Error
from utils.database import create_connection

def create_event(user_id, title, description):
    """
    Erstellt ein neues Event in der Datenbank.
    :param user_id: Die ID des Benutzers
    :param title: Der Titel des Events
    :param description: Die Beschreibung des Events
    """
    if title:
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO events (user_id, title, description) VALUES (?, ?, ?)",
                    (user_id, title, description),
                )
                conn.commit()
                st.success("Event erfolgreich erstellt!")
            except Error as e:
                st.error(f"Fehler beim Erstellen des Events: {e}")
            finally:
                conn.close()
    else:
        st.error("Der Titel des Events darf nicht leer sein.")

def edit_event(event_id, new_title, new_description):
    """
    Bearbeitet ein vorhandenes Event.
    :param event_id: Die ID des Events
    :param new_title: Der neue Titel des Events
    :param new_description: Die neue Beschreibung des Events
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE events SET title = ?, description = ? WHERE id = ?",
                (new_title, new_description, event_id),
            )
            conn.commit()
            st.success("Event erfolgreich bearbeitet!")
        except Error as e:
            st.error(f"Fehler beim Bearbeiten des Events: {e}")
        finally:
            conn.close()

def delete_event(event_id):
    """
    Löscht ein Event aus der Datenbank.
    :param event_id: Die ID des Events
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            st.success("Event erfolgreich gelöscht!")
        except Error as e:
            st.error(f"Fehler beim Löschen des Events: {e}")
        finally:
            conn.close()

def create_task(event_id, title, content):
    """
    Erstellt eine neue Aufgabe (Task) für ein Event.
    :param event_id: Die ID des Events
    :param title: Der Titel der Aufgabe
    :param content: Der Inhalt der Aufgabe
    """
    if title:
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (event_id, title, content) VALUES (?, ?, ?)",
                    (event_id, title, content),
                )
                conn.commit()
                st.success("Aufgabe erfolgreich erstellt!")
            except Error as e:
                st.error(f"Fehler beim Erstellen der Aufgabe: {e}")
            finally:
                conn.close()
    else:
        st.error("Der Titel der Aufgabe darf nicht leer sein.")

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
            st.success("Aufgabe erfolgreich gelöscht!")
        except Error as e:
            st.error(f"Fehler beim Löschen der Aufgabe: {e}")
        finally:
            conn.close()

def load_events(user_id):
    """
    Lädt alle Events eines Benutzers aus der Datenbank.
    :param user_id: Die ID des Benutzers
    :return: Liste der Events
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description FROM events WHERE user_id = ?", (user_id,))
            events = cursor.fetchall()
            return events
        except Error as e:
            st.error(f"Fehler beim Laden der Events: {e}")
        finally:
            conn.close()
    return []

def load_tasks(event_id):
    """
    Lädt alle Aufgaben (Tasks) für ein bestimmtes Event.
    :param event_id: Die ID des Events
    :return: Liste der Aufgaben
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, status FROM tasks WHERE event_id = ?", (event_id,))
            tasks = cursor.fetchall()
            return tasks
        except Error as e:
            st.error(f"Fehler beim Laden der Aufgaben: {e}")
        finally:
            conn.close()
    return []

def share_event(event_id, shared_by_user_id, shared_with_username):
    """
    Teilt ein Event mit einem anderen Benutzer.
    :param event_id: Die ID des Events
    :param shared_by_user_id: Die ID des Benutzers, der das Event teilt
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
                # Füge das geteilte Event in die Datenbank ein
                cursor.execute(
                    "INSERT INTO shared_events (event_id, shared_by_user_id, shared_with_user_id) VALUES (?, ?, ?)",
                    (event_id, shared_by_user_id, shared_with_user_id),
                )
                conn.commit()
                st.success(f"Event erfolgreich mit {shared_with_username} geteilt!")
            else:
                st.error(f"Benutzer '{shared_with_username}' nicht gefunden.")
        except Error as e:
            st.error(f"Fehler beim Teilen des Event: {e}")
        finally:
            conn.close()

def load_shared_events(user_id):
    """
    Lädt die mit dem Benutzer geteilten Events.
    :param user_id: Die ID des Benutzers
    :return: Liste der geteilten Events (Event-ID, Event-Titel, Name des Teilers)
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT events.id, events.title, users.username
                FROM shared_events
                JOIN events ON shared_events.event_id = events.id
                JOIN users ON shared_events.shared_by_user_id = users.id
                WHERE shared_events.shared_with_user_id = ?
            """, (user_id,))
            shared_events = cursor.fetchall()
            return shared_events
        except Error as e:
            st.error(f"Fehler beim Laden der geteilten Events: {e}")
        finally:
            conn.close()
    return []