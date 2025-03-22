import sqlite3
from sqlite3 import Error
from utils.database import create_connection
from datetime import datetime
import streamlit as st

def save_stats(user_id, event_id, score):
    """
    Speichert die Statistik für eine Quiz-Session eines Events.
    :param user_id: Die ID des Benutzers
    :param event_id: Die ID des Events
    :param score: Die erreichte Punktzahl
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO stats (user_id, event_id, score, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, event_id, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        except Error as e:
            st.error(f"Fehler beim Speichern der Statistik: {e}")
        finally:
            conn.close()

def load_stats(user_id, event_id=None):
    """
    Lädt die Statistiken für einen Benutzer, optional gefiltert nach einem bestimmten Event.
    :param user_id: Die ID des Benutzers
    :param event_id: Die ID des Events (optional)
    :return: Eine Liste von Statistiken (Event-Titel, Punktzahl, Datum)
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if event_id:
                # Lade Statistiken für ein bestimmtes Event
                cursor.execute("""
                    SELECT events.title, stats.score, stats.timestamp
                    FROM stats
                    JOIN events ON stats.event_id = events.id
                    WHERE stats.user_id = ? AND stats.event_id = ?
                    ORDER BY stats.timestamp DESC
                """, (user_id, event_id))
            else:
                # Lade alle Statistiken des Benutzers
                cursor.execute("""
                    SELECT events.title, stats.score, stats.timestamp
                    FROM stats
                    JOIN events ON stats.event_id = events.id
                    WHERE stats.user_id = ?
                    ORDER BY stats.timestamp DESC
                """, (user_id,))
            stats = cursor.fetchall()
            return stats
        except Error as e:
            st.error(f"Fehler beim Laden der Statistiken: {e}")
        finally:
            conn.close()
    return []

def calculate_event_performance(user_id, event_id):
    """
    Berechnet die durchschnittliche Punktzahl für ein bestimmtes Event.
    :param user_id: Die ID des Benutzers
    :param event_id: Die ID des Events
    :return: Durchschnittliche Punktzahl
    """
    stats = load_stats(user_id, event_id)
    if stats:
        total_score = sum(stat[1] for stat in stats)
        average_score = total_score / len(stats)
        return average_score
    return 0

def display_event_statistics(user_id, event_id):
    stats = load_stats(user_id, event_id)
    if stats:
        st.write("### Statistiken für das Event:")
        for stat in stats:
            st.write(f"**Event:** {stat[0]}, **Punktzahl:** {stat[1]}, **Datum:** {stat[2]}")

        # Berechne die durchschnittliche Punktzahl
        total_score = sum(stat[1] for stat in stats)
        average_score = total_score / len(stats)
        st.write(f"**Durchschnittliche Punktzahl:** {average_score:.2f}")

        # Zeige die Entwicklung der Punktzahl über die Zeit an
        st.write("### Entwicklung der Punktzahl über die Zeit")
        dates = [stat[2] for stat in stats]
        scores = [stat[1] for stat in stats]
        st.line_chart({"Punktzahl": scores}, use_container_width=True)
    else:
        st.warning("Keine Statistiken für dieses Event gefunden.")