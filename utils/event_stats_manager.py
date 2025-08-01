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
        paper_bgcolor='rgba(0,0,0,0)',
        font_color="#E0E0E0" if st.session_state.get("dark_mode", False) else "#333333"
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

from utils.auth import PRIMARY_COLOR, ACCENT_COLOR, TEXT_COLOR

def display_event_statistics(user_id, event_id=None):
    st.header("📊 Fortschritt & Statistiken")

    
    st.markdown(f"""
    <style>
        .score-card {{
            background-color: white;
            border-left: 6px solid {PRIMARY_COLOR};
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}
        .score-badge {{
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 20px;
            color: #28a745;
        }}
        .excellent {{ background-color: #4CAF50; }}
        .good {{ background-color: #8BC34A; }}
        .average {{ background-color: #FFC107; color: black; }}
        .poor {{ background-color: #F44336; }}
        .tip-box {{
            background-color: #fffdf3;
            border-left: 5px solid {ACCENT_COLOR};
            padding: 12px 16px;
            margin: 12px 0;
            border-radius: 8px;
            font-size: 0.95rem;
        }}
        .section-header {{
            margin-top: 30px;
            margin-bottom: 10px;
            font-size: 20px;
            font-weight: 600;
            color: {TEXT_COLOR};
        }}
    </style>
    """, unsafe_allow_html=True)

    # 📌 Kontext: Event oder Übersicht
    if event_id:
        event = get_event_by_id(event_id)
        event_title = event[1]
        st.subheader(f"📅 Event: {event_title}")
        tasks = get_tasks_by_event_id(event_id)
        all_stats = load_stats(user_id, event_id=event_id)
    else:
        st.subheader("🌍 Gesamtübersicht aller Events")
        all_stats = load_stats(user_id)

    if not all_stats:
        st.info("Noch keine Statistiken vorhanden.")
        return

    # 🔢 Durchschnitt berechnen
    avg_score = calculate_average_score(all_stats)
    status, badge_class = calculate_progress_status(avg_score)

    # 🧾 Anzeige Gesamtscore
    st.markdown(f"""
        <div class="score-card">
            <h4>🔢 Gesamtdurchschnitt</h4>
            <div class="score-badge {badge_class}">
                {avg_score:.1f}% – {status}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 💡 Vorschläge bei schlechtem Schnitt
    if avg_score < 65:
        st.markdown('<div class="section-header">💡 Verbesserungsvorschläge</div>', unsafe_allow_html=True)
        tips = generate_event_tips(avg_score, event_title if event_id else "deine Themen")
        for tip in tips:
            st.markdown(f"<div class='tip-box'>{tip}</div>", unsafe_allow_html=True)

    # 📈 Score-Verlauf
    if len(all_stats) >= 2:
        df = pd.DataFrame(all_stats, columns=['event_title', 'score', 'task_id', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values("timestamp")
        fig = px.line(
            df, x="timestamp", y="score",
            title="📈 Score-Verlauf",
            markers=True,
            labels={"score": "Punktzahl", "timestamp": "Zeit"}
        )
        fig.update_layout(yaxis_range=[0, 100], height=400)
        st.plotly_chart(fig, use_container_width=True)

    # 📋 Detailübersicht nach Aufgaben
    st.markdown('<div class="section-header">📝 Aufgaben im Detail</div>', unsafe_allow_html=True)
    task_scores = defaultdict(list)
    for title, score, task_id, timestamp in all_stats:
        task_scores[task_id].append((title, score, timestamp))

    for task_id, results in task_scores.items():
        task = get_task_by_id(task_id)
        if task:
            _, _, task_title, _, _ = task
            with st.expander(f"📌 Aufgabe: {task_title}"):
                for _, score, ts in results[:5]:
                    label, badge_class = calculate_progress_status(score)
                    st.markdown(
                        f"<span class='score-badge {badge_class}'>{score}%</span> – {ts[:16].replace('T', ' um ')}",
                        unsafe_allow_html=True
                    )
                st.markdown(" ")
                if st.button("🧩 Quiz erneut starten", key=f"retry_{task_id}"):
                    st.session_state.update({
                        "selected_event_id": task[1],
                        "selected_task_id": task_id,
                        "main_navigation": "Rätsel"
                    })
                    st.rerun()