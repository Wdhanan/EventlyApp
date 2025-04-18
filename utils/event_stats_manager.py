import sqlite3
from sqlite3 import Error
from utils.database import create_connection
from datetime import datetime
import streamlit as st

from utils.event_manager import load_tasks

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
        st.markdown('<h3 style="margin-top:1.5rem;">📊 Die letzten 3 Quiz-Ergebnisse</h3>', unsafe_allow_html=True)
        
        # Get the last 3 quiz results for each task
        tasks = load_tasks(event_id)
        
        if not tasks:
            st.info("Keine Aufgaben für dieses Event gefunden.")
            return
            
        # Create a dictionary to store task stats
        task_stats = {}
        
        for task in tasks:
            task_id = task[0]
            task_title = task[1]
            
            # Get stats for this specific task
            task_specific_stats = [stat for stat in stats if stat[2] == task_id]
            last_three = task_specific_stats[-3:] if task_specific_stats else []
            
            # Store in dictionary
            task_stats[task_id] = {
                "title": task_title,
                "last_three": last_three
            }
        
        # Now display the results in a nice table
        st.markdown('<table class="stats-table">', unsafe_allow_html=True)
        st.markdown('<tr><th>Aufgabe</th><th>Neustes Quiz</th><th>Vorletztes Quiz</th><th>Drittletztes Quiz</th><th>Trend</th></tr>', unsafe_allow_html=True)
        
        for task_id, data in task_stats.items():
            title = data["title"]
            results = data["last_three"]
            
            # Format results
            result_cells = []
            for i in range(3):
                if i < len(results):
                    score = results[-(i+1)][1]  # Get the score, starting from newest
                    status, color = calculate_progress_status(score)
                    result_cells.append(f'<td><span style="color:{color}; font-weight:bold;">{score}%</span><br><small>{status}</small></td>')
                else:
                    result_cells.append('<td>-</td>')
            
            # Calculate trend
            trend = ""
            if len(results) >= 2:
                newest = results[-1][1]
                previous = results[-2][1]
                if newest > previous:
                    trend = '📈 <span style="color:green">+' + f"{newest - previous:.1f}%" + '</span>'
                elif newest < previous:
                    trend = '📉 <span style="color:red">' + f"{newest - previous:.1f}%" + '</span>'
                else:
                    trend = '📊 <span style="color:gray">±0%</span>'
            
            # Output row
            st.markdown(f'<tr><td>{title}</td>{result_cells[0]}{result_cells[1]}{result_cells[2]}<td>{trend}</td></tr>', unsafe_allow_html=True)
            
        st.markdown('</table>', unsafe_allow_html=True)
    else:
        st.info("Noch keine Quiz zu diesem Event durchgeführt.")