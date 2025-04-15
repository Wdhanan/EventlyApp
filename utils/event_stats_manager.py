import sqlite3
from sqlite3 import Error
from utils.database import create_connection
from datetime import datetime
import streamlit as st

def save_stats(user_id, event_id, score):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO stats (user_id, event_id, score, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, event_id, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        except Error as e:
            st.error(f"Fehler beim Speichern der Statistik: {e}")
        finally:
            conn.close()

def load_stats(user_id, event_id=None):
    """
    Lädt die Statistiken für einen Benutzer, optional gefiltert nach einem bestimmten Event.
    Berücksichtigt sowohl eigene als auch geteilte Events.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if event_id:
                # Lade Statistiken für ein bestimmtes Event (auch geteilte)
                cursor.execute("""
                    SELECT events.title, stats.score, stats.timestamp
                    FROM stats
                    JOIN events ON stats.event_id = events.id
                    WHERE stats.user_id = ? AND stats.event_id = ?
                    ORDER BY stats.timestamp DESC
                """, (user_id, event_id))
            else:
                # Lade alle Statistiken des Benutzers (eigene und geteilte Events)
                cursor.execute("""
                    SELECT events.title, stats.score, stats.timestamp
                    FROM stats
                    JOIN events ON stats.event_id = events.id
                    WHERE stats.user_id = ?
                    UNION
                    SELECT events.title, stats.score, stats.timestamp
                    FROM stats
                    JOIN events ON stats.event_id = events.id
                    JOIN shared_events ON events.id = shared_events.event_id
                    WHERE shared_events.shared_with_user_id = ?
                    ORDER BY timestamp DESC
                """, (user_id, user_id))
            stats = cursor.fetchall()
            return stats
        except Error as e:
            st.error(f"Fehler beim Laden der Statistiken: {e}")
        finally:
            conn.close()
    return []

def calculate_progress_status(score):
    if score < 20:
        return "❌ Schlecht", "inverse"  # Rot als inverse Farbe
    elif score < 50:
        return "⚠️ Verbesserung nötig", "normal"  # Orange als normale Farbe
    elif score < 75:
        return "👍 Gut", "normal"  # Blau als normale Farbe
    else:
        return "✅ Ausgezeichnet", "normal"  # Grün als normale Farbe

def display_event_statistics(user_id, event_id):
    stats = load_stats(user_id, event_id)
    if stats:
        st.markdown("### 📊 Event Fortschritt")
        
        # Erstelle eine schöne Tabelle mit Fortschrittsdaten
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Durchschnittliche Punktzahl
            total_score = sum(stat[1] for stat in stats)
            average_score = total_score / len(stats)
            status, color = calculate_progress_status(average_score)
            
            st.metric("Durchschnittliche Punktzahl", 
                     f"{average_score:.1f}%", 
                     delta=status,
                     delta_color=color)
            
            # Letzte Bewertung
            last_score = stats[0][1]
            status, color = calculate_progress_status(last_score)
            
            st.metric("Letzte Bewertung", 
                     f"{last_score}%", 
                     delta=status,
                     delta_color=color)
        
        with col2:
            # Detailtabelle mit allen Versuchen
            st.markdown("### 📅 Versuchsverlauf")
            
            # Vorbereitung der Daten für die Tabelle
            table_data = []
            for stat in stats:
                status, _ = calculate_progress_status(stat[1])
                table_data.append({
                    "Datum": stat[2],
                    "Punktzahl": f"{stat[1]}%",
                    "Status": status
                })
            
            # Erstelle eine schöne Tabelle mit Streamlit
            st.table(table_data)
    else:
        st.warning("Keine Statistiken für dieses Event gefunden.")