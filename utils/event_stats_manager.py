from sqlite3 import Error
import streamlit as st
from collections import defaultdict
import pandas as pd
import plotly.express as px
from utils.database import (
    create_connection,
    get_event_by_id,
    get_tasks_by_event_id,
    get_task_by_id,
    get_username_by_id,
)

# Konstanten für Pagination
ITEMS_PER_PAGE = 5

def save_stats(user_id, event_id, task_id, score):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stats (user_id, event_id, task_id, score, timestamp)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (user_id, event_id, task_id, score))
            conn.commit()
        except Error as e:
            print(f"Fehler beim Speichern der Statistik: {e}")
        finally:
            conn.close()

def load_stats(user_id, event_id=None, task_id=None, limit=None, offset=0):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            query = """
                SELECT events.title, stats.score, stats.task_id, stats.timestamp
                FROM stats
                JOIN events ON stats.event_id = events.id
                WHERE stats.user_id = ?
            """
            params = [user_id]

            if event_id and task_id:
                query += " AND stats.event_id = ? AND stats.task_id = ?"
                params.extend([event_id, task_id])
            elif event_id:
                query += " AND stats.event_id = ?"
                params.append(event_id)
            
            query += " ORDER BY stats.timestamp DESC"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Fehler beim Laden der Statistiken: {e}")
        finally:
            conn.close()
    return []

def calculate_progress_status(score):
    if score >= 80:
        return "Ausgezeichnet", "score-badge-excellent"
    elif score >= 65:
        return "Gut", "score-badge-good"
    elif score >= 50:
        return "Durchschnittlich", "score-badge-average"
    else:
        return "Schwach", "score-badge-poor"

def generate_event_tips(score, event_title):
    tips = []
    if score < 50:
        tips.append(f"📌 **Grundlagen vertiefen**: Wiederhole die Kernkonzepte des Events '{event_title}'.")
        tips.append(f"🔍 **Details beachten**: Achte auf spezifische Anforderungen im Event '{event_title}'.")
        tips.append(f"🔄 **Praxis üben**: Versuche das Event erneut mit Fokus auf die Problembereiche.")
    elif score < 65:
        tips.append(f"🎯 **Schwerpunkte setzen**: Identifiziere die wichtigsten Aspekte von '{event_title}'.")
        tips.append(f"📝 **Zusammenfassungen erstellen**: Fasse die Schlüsselinformationen des Events zusammen.")
    return tips

def calculate_average_score(stats):
    if not stats:
        return 0
    return sum(stat[1] for stat in stats) / len(stats)

def display_progress_chart(task_stats):
    if len(task_stats) < 2:
        return
    
    df = pd.DataFrame(task_stats, columns=['title', 'score', 'task_id', 'timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = px.line(
        df, 
        x='timestamp', 
        y='score', 
        title='Fortschrittsverlauf',
        markers=True,
        labels={'score': 'Punktzahl (%)', 'timestamp': 'Datum'}
    )
    fig.update_layout(
        yaxis_range=[0, 100],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

def display_pagination(total_items, items_per_page, page_key):
    total_pages = (total_items + items_per_page - 1) // items_per_page
    if total_pages <= 1:
        return 0
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.number_input(
            "Seite", 
            min_value=1, 
            max_value=total_pages, 
            value=1,
            key=f"page_{page_key}"
        )
    return (page - 1) * items_per_page

def display_event_statistics(user_id, event_id=None):
    st.header("📊 Lernfortschritt & Statistiken")
    
    # CSS für die Bewertungs-Badges
    st.markdown("""
    <style>
        .score-badge-excellent {
            background-color: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
            margin: 5px 0;
        }
        .score-badge-good {
            background-color: #8BC34A;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
            margin: 5px 0;
        }
        .score-badge-average {
            background-color: #FFC107;
            color: black;
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
            margin: 5px 0;
        }
        .score-badge-poor {
            background-color: #F44336;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
            margin: 5px 0;
        }
        .progress-container {
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            background-color: #f8f9fa;
        }
        .tip-box {
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 4px 4px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    if event_id:
        event = get_event_by_id(event_id)
        if event:
            event_title = event[1]
            st.subheader(f"📅 {event_title}")
            tasks = get_tasks_by_event_id(event_id)
            
            # Lade alle Statistiken für Pagination
            all_stats = load_stats(user_id, event_id)
            stats_by_task = defaultdict(list)
            for stat in all_stats:
                task_id = stat[2]
                if task_id is not None:
                    stats_by_task[task_id].append(stat)

            # Gesamtfortschritt für das Event
            event_stats = []
            for task in tasks:
                task_stats = stats_by_task.get(task[0], [])
                if task_stats:
                    event_stats.extend(task_stats)
            
            if event_stats:
                avg_score = calculate_average_score(event_stats)
                status_label, css_class = calculate_progress_status(avg_score)
                st.markdown(f"""
                <div class="progress-container">
                    <h4>Gesamtfortschritt</h4>
                    <span class="{css_class}">Durchschnitt: <strong>{avg_score:.1f}%</strong> ({status_label})</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Tipps für das gesamte Event
                if avg_score < 65:
                    tips = generate_event_tips(avg_score, event_title)
                    if tips:
                        st.markdown("### 💡 Event-spezifische Verbesserungsvorschläge")
                        for tip in tips:
                            st.markdown(f"<div class='tip-box'>{tip}</div>", unsafe_allow_html=True)
            
            # Pagination für Aufgaben
            total_tasks = len(tasks)
            offset = display_pagination(total_tasks, ITEMS_PER_PAGE, "tasks")
            displayed_tasks = tasks[offset:offset + ITEMS_PER_PAGE]
            
            for task in displayed_tasks:
                task_id, _, task_name, _, _ = task
                task_stats = stats_by_task.get(task_id, [])
                
                with st.expander(f"📝 {task_name}", expanded=True):
                    if task_stats:
                        # Letzte 3 Versuche anzeigen
                        recent_stats = task_stats[:3]
                        avg_score = calculate_average_score(recent_stats)
                        status_label, css_class = calculate_progress_status(avg_score)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f"""
                            <div style="margin-bottom: 15px;">
                                <h4>Letzte Versuche</h4>
                                <span class="{css_class}">Durchschnitt: <strong>{avg_score:.1f}%</strong></span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            for stat in recent_stats:
                                _, score, _, timestamp = stat
                                username = get_username_by_id(user_id)
                                status_label, css_class = calculate_progress_status(score)
                                st.markdown(
                                    f"<span class='{css_class}'>{score}% am {timestamp}</span>",
                                    unsafe_allow_html=True
                                )
                        
                        with col2:
                            display_progress_chart(task_stats)
                    else:
                        st.info("Noch keine Statistiken für diese Aufgabe vorhanden.")
        else:
            st.error("Event nicht gefunden.")
    else:
        st.subheader("📅 Alle Statistiken")
        all_stats = load_stats(user_id)
        
        if all_stats:
            # Pagination für alle Statistiken
            total_stats = len(all_stats)
            offset = display_pagination(total_stats, ITEMS_PER_PAGE, "all_stats")
            displayed_stats = all_stats[offset:offset + ITEMS_PER_PAGE]
            
            for stat in displayed_stats:
                _, score, task_id, timestamp = stat
                task = get_task_by_id(task_id)
                if task:
                    _, ev_id, task_name, _, _ = task
                    event = get_event_by_id(ev_id)
                    username = get_username_by_id(user_id)
                    status_label, css_class = calculate_progress_status(score)
                    st.markdown(
                        f"<span class='{css_class}'>{username}: <strong>{score}%</strong> für '{task_name}' ({event[1]}) am {timestamp}</span>",
                        unsafe_allow_html=True
                    )
        else:
            st.info("Keine Statistiken vorhanden.")
