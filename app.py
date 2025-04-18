import streamlit as st
from dotenv import load_dotenv
from utils.auth import register, login, logout, load_all_users
from utils.event_manager import create_event, edit_event, delete_event, load_events, load_shared_events, load_tasks, share_event
from utils.task_manager import save_task, edit_task, delete_task, load_shared_tasks
from utils.event_question_generator import quiz_mode
from utils.event_stats_manager import calculate_progress_status, load_stats, display_event_statistics
import os
import pandas as pd
import io
import base64


PAGE_IMAGES = {
    "Dashboard": "https://img.icons8.com/fluency/96/dashboard-layout.png",
    "Events": "https://img.icons8.com/fluency/96/calendar.png",
    "Tasks": "https://img.icons8.com/fluency/96/todo-list.png",
    "Rätsel": "https://img.icons8.com/fluency/96/quiz.png",
    "Statistiken": "https://img.icons8.com/fluency/96/graph.png",
    "Profil": "https://img.icons8.com/fluency/96/user.png",
    "Einstellungen": "https://img.icons8.com/fluency/96/settings.png",
    "Über die Anwendung": "https://img.icons8.com/fluency/96/info.png",
    "Export": "https://img.icons8.com/fluency/96/export.png" 
}

def display_page_header(title):
    col1, col2 = st.columns([1, 10])
    with col1:
        if title in PAGE_IMAGES:
            st.image(PAGE_IMAGES[title], width=60)
    with col2:
        st.header(f"{NAV_ICONS.get(title, '')} {title}")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# Create a new function for downloading files
def create_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href


# Design-Konstanten
PRIMARY_COLOR = "#4A90E2"
SECONDARY_COLOR = "#F5F5F5"
ACCENT_COLOR = "#FFA500"
DARK_BG = "#1E1E1E"
DARK_CARD = "#2D2D2D"

# Umgebungsvariablen laden
load_dotenv()

NAV_ICONS = {
    "Dashboard": "📊",
    "Events": "📅", 
    "Tasks": "✅",
    "Rätsel": "🧩",
    "Statistiken": "📈",
    "Profil": "👤",
    "Einstellungen": "⚙️",
    "Über die Anwendung": "ℹ️",
    "Login": "🔑",
    "Registrierung": "📝",
    "API-Key bearbeiten": "🔧",
    "Export" : "📤",
    "API-Key konfigurieren": "🔧"
}

BACKGROUND_CSS = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("assets/images/background.jpg");
    background-size: cover;
    background-attachment: fixed;
}}

.auth-bg {{
    background-image: url("assets/images/auth-bg.jpg");
    background-size: cover;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}}
</style>
"""

LOGIN_CSS = """
<style>
/* Text center helper */
.text-center {
    text-align: center;
    margin-top: 1rem;
}

/* Login/Registration Form Fixes */
div.block-container {
    padding-top: 1rem !important;
    max-width: 500px !important;
    margin: 0 auto;
}

.auth-form-container {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-top: 1rem !important;
    margin-bottom: 1rem !important;
}

/* Remove all extra padding/spacing */
.auth-form-container > div {
    margin-bottom: 1rem !important;
}

/* Make the form inputs more compact */
.auth-form-container .stTextInput, 
.auth-form-container .stButton {
    margin-bottom: 0.75rem !important;
}

/* Fix for the header */
.auth-form-container h1, 
.auth-form-container h2, 
.auth-form-container h3 {
    margin-top: 0 !important;
    padding-top: 0 !important;
    margin-bottom: 1.5rem !important;
}

/* Hide the extra white block */
div[data-testid="stVerticalBlock"] > div:empty {
    display: none !important;
}
</style>
"""

# --- CSS-STYLE ---
MAIN_CSS = f"""
<style>
:root {{
    --primary: {PRIMARY_COLOR};
    --secondary: {SECONDARY_COLOR};
    --accent: {ACCENT_COLOR};
    --dark-bg: {DARK_BG};
    --dark-card: {DARK_CARD};
    --border-radius: 12px;
    --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    --transition: all 0.3s ease;
}}

/* Globale Styles */
.stApp {{
    background-color: var(--secondary);
    color: #333;
    line-height: 1.6;
}}

.stHeader {{
    color: var(--primary) !important;
}}

/* Dark Mode */
.dark-mode .stApp {{
    background-color: var(--dark-bg) !important;
    color: white !important;
}}

.dark-mode .card {{
    background-color: var(--dark-card) !important;
}}

/* Cards */
.card {{
    background: white;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-left: 4px solid var(--primary);
    transition: var(--transition);
}}

.card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}}

.shared-card {{
    border-left: 4px solid var(--accent);
}}

/* Buttons */
.stButton>button {{
    background-color: var(--primary) !important;
    color: white !important;
    border-radius: var(--border-radius) !important;
    padding: 0.5rem 1.5rem !important;
    border: none !important;
    transition: var(--transition) !important;
}}

.stButton>button:hover {{
    background-color: #3a7bc8 !important;
    transform: translateY(-2px) !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: linear-gradient(135deg, var(--primary), #6a11cb) !important;
}}

[data-testid="stSidebar"] .stRadio label {{
    color: white !important;
    padding: 0.75rem 1rem !important;
    margin: 0.25rem 0 !important;
    border-radius: var(--border-radius) !important;
    transition: var(--transition) !important;
}}

[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(255, 255, 255, 0.1) !important;
}}

[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label {{
    background: rgba(255, 255, 255, 0.2) !important;
    font-weight: 600 !important;
}}

/* Task Items */
.task-item {{
    background: #f0f7ff;
    padding: 0.75rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    transition: var(--transition);
}}

.task-item:hover {{
    background: #e0f0ff;
}}

.dark-mode .task-item {{
    background: #2a3d5c !important;
}}

/* Divider */
.divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, var(--primary), transparent);
    margin: 1.5rem 0;
    border: none;
}}

/* Hide empty white block */
div[data-testid="stVerticalBlock"]:has(> div.element-container:empty) {{
    display: none;
}}

/* Fix empty space above forms */
div.block-container {{
    padding-top: 1rem !important;
}}

/* Fix spacing around form elements */
div.element-container {{
    margin-bottom: 0 !important;
}}

/* Make form appear closer to top */
.auth-form-container {{
    margin-top: 0 !important;
}}
</style>
"""


HEADER_FIX_CSS = """
/* Fix headers */
<style>
h1, h2, h3, h4, h5, h6 {
    margin-top: 0.5rem !important;
    padding-top: 0.5rem !important;
    line-height: 1.3 !important;
    overflow: visible !important;
    white-space: normal !important;
}

/* Add more space for content */
[data-testid="stAppViewContainer"] > div:nth-child(1) > div > div > div:nth-child(2) {
    padding-top: 1.5rem !important;
}
</style>
"""

MAIN_CSS = f"""
{MAIN_CSS}
{LOGIN_CSS}
{HEADER_FIX_CSS}
"""


st.markdown(MAIN_CSS, unsafe_allow_html=True)
# Zustandsvariablen initialisieren mit Default-Werten
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "api_key_configured" not in st.session_state:
    st.session_state.api_key_configured = os.getenv("DEEPSEEK_API_KEY") is not None
if "deepseek_api_key" not in st.session_state:
    st.session_state.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "main_navigation" not in st.session_state:
    st.session_state.main_navigation = "Dashboard"
if "show_login" not in st.session_state:
    st.session_state.show_login = True
if "show_register" not in st.session_state:
    st.session_state.show_register = False

st.sidebar.title(f"{NAV_ICONS['Dashboard']} Navigation")

if not st.session_state["api_key_configured"]:
    page = st.sidebar.radio(
        "Wähle eine Seite",
        ["API-Key konfigurieren"],
        format_func=lambda x: f"{NAV_ICONS[x]} {x}",
        key="pre_auth_navigation"  
    )
else:
    if not st.session_state["logged_in"]:
        page = st.sidebar.radio(
            "Wähle eine Seite",
            ["Login", "Registrierung", "API-Key bearbeiten"],
            format_func=lambda x: f"{NAV_ICONS[x]} {x}",
            index=0 if st.session_state.get("show_login", True) else 1,
            key="auth_navigation_sidebar"  
        )
        if page == "Login" and not st.session_state.get("show_login", True):
            st.session_state["show_login"] = True
            st.session_state["show_register"] = False
            st.rerun()
        elif page == "Registrierung" and st.session_state.get("show_login", True):
            st.session_state["show_login"] = False
            st.session_state["show_register"] = True
            st.rerun()


    else:
        available_pages = ["Dashboard", "Events", "Tasks", "Rätsel", "Statistiken", "Profil", "Einstellungen","Export", "Über die Anwendung"]
        
        
        # Initialisiere main_navigation falls nicht vorhanden oder ungültig
        if "main_navigation" not in st.session_state or st.session_state["main_navigation"] not in available_pages:
            st.session_state["main_navigation"] = "Dashboard"
            
        # Erstelle Radio-Buttons mit aktueller Auswahl
        selected_page = st.sidebar.radio(
            "Navigation",
            available_pages,
            index=available_pages.index(st.session_state["main_navigation"]),
            format_func=lambda x: f"{NAV_ICONS[x]} {x}",
            key="main_nav_radio"
        )
        
        # Aktualisiere die Session State nur wenn sich die Auswahl ändert
        if selected_page != st.session_state["main_navigation"]:
            st.session_state["main_navigation"] = selected_page
            st.rerun()
            
        page = st.session_state["main_navigation"]
            

# Hauptinhalt basierend auf der ausgewählten Seite
if page == "API-Key konfigurieren" or page == "API-Key bearbeiten":
    display_page_header("API-Key konfigurieren")
    with st.container():
        with st.container():
            st.write("""
                Um den EventManager zu nutzen, benötigst du einen DeepSeek API-Key. 
                Gehe auf [OpenRouter](https://openrouter.ai), erstelle ein kostenloses Konto und generiere einen API-Key für DeepSeek.
                Gib den Key unten ein, um fortzufahren.
            """)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                api_key = st.text_input("Gib deinen DeepSeek API-Key ein", value=st.session_state["deepseek_api_key"], key="api_key_input")
                if st.button("API-Key speichern", key="save_api_key_button"):
                    if api_key:
                        with open(".env", "w") as env_file:
                            env_file.write(f"DEEPSEEK_API_KEY={api_key}")
                        st.session_state["api_key_configured"] = True
                        st.session_state["deepseek_api_key"] = api_key
                        st.success("API-Key erfolgreich gespeichert!")
                        load_dotenv(override=True)
                    else:
                        st.error("Bitte gib einen gültigen API-Key ein.")

elif not st.session_state["logged_in"]:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa !important;
        background-image: none !important; 
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("show_login", True):
        login()
    else:
        register()


else:
    if page == "Dashboard":
        display_page_header("Dashboard")
        
        # Modernes, sauberes CSS
        st.markdown("""
        <style>
        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stats-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }
        .section-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #4A90E2;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #eee;
        }
        .event-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.2rem;
            margin-top: 1rem;
        }
        .event-card {
            background: white;
            border-radius: 10px;
            padding: 1.2rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            border-left: 3px solid #4A90E2;
            transition: all 0.2s ease;
        }
        .shared-event-card {
            border-left: 3px solid #FFA500;
        }
        .event-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .event-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .event-name {
            font-weight: 600;
            font-size: 1.1rem;
            color: #333;
        }
        .event-shared {
            font-size: 0.8rem;
            color: #FFA500;
            background: #FFF5E6;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }
        .event-description {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
            line-height: 1.4;
        }
        .section-label {
            font-size: 0.8rem;
            color: #888;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .task-list {
            margin: 0.8rem 0;
        }
        .task-item {
            padding: 0.4rem 0.6rem;
            margin: 0.2rem 0;
            background: #F8F9FA;
            border-radius: 4px;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
        }
        .task-item:before {
            content: "•";
            color: #4A90E2;
            margin-right: 0.5rem;
        }
        .progress-container {
            margin: 0.8rem 0;
        }
        .progress-score {
            font-size: 1.2rem;
            font-weight: 600;
            color: #4A90E2;
            text-align: center;
        }
        .progress-label {
            font-size: 0.8rem;
            color: #888;
            text-align: center;
            margin-bottom: 0.3rem;
        }
        .action-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.8rem;
        }
        .primary-btn {
            flex: 1;
            background: #4A90E2 !important;
            color: white !important;
            border: none !important;
        }
        .secondary-btn {
            flex: 1;
            background: #F0F0F0 !important;
            color: #333 !important;
            border: none !important;
        }
        .pagination-controls {
            display: flex;
            justify-content: center;
            margin-top: 1.5rem;
            gap: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Statistische Übersicht
        with st.container():
            st.markdown('<div class="stats-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📊 Deine Aktivitäten</div>', unsafe_allow_html=True)
            
            stats = load_stats(st.session_state["user_id"])
            events = load_events(st.session_state["user_id"])
            num_events = len(events) if events else 0
            num_quizzes = len(stats) if stats else 0
            
            cols = st.columns(3)
            metrics = [
                ("Meine Events", num_events, "Anzahl der von dir erstellten Events"),
                ("Durchgeführte Quizze", num_quizzes, "Anzahl der durchgeführten Quizze"),
                ("Durchschnittsnote", f"{sum(stat[1] for stat in stats)/num_quizzes:.1f}%" if stats else "0%", "Deine durchschnittliche Quiz-Punktzahl")
            ]
            
            for col, (label, value, help_text) in zip(cols, metrics):
                with col:
                    st.metric(label, value, help=help_text)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Eigene Events
        with st.container():
            st.markdown('<div class="stats-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📌 Meine Events</div>', unsafe_allow_html=True)
            
            if events:
                # Pagination
                items_per_page = 2
                total_pages = (len(events) + items_per_page - 1) // items_per_page
                page_number = st.number_input('Seite', min_value=1, max_value=total_pages, value=1, key='events_page')
                start_idx = (page_number - 1) * items_per_page
                end_idx = start_idx + items_per_page
                
                # Events Grid
                st.markdown('<div class="event-grid">', unsafe_allow_html=True)
                for event in events[start_idx:end_idx]:
                    event_id, title, description = event[0], event[1], event[2]
                    
                    st.markdown('<div class="event-card">', unsafe_allow_html=True)
                    
                    # Event Header
                    st.markdown('<div class="event-header">', unsafe_allow_html=True)
                    st.markdown(f'<div class="event-name">{title}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Beschreibung
                    st.markdown(f'<div class="event-description">{description or "Keine Beschreibung"}</div>', unsafe_allow_html=True)
                    
                    # Aufgaben
                    tasks = load_tasks(event_id)
                    if tasks:
                        st.markdown('<div class="section-label">Aufgaben</div>', unsafe_allow_html=True)
                        st.markdown('<div class="task-list">', unsafe_allow_html=True)
                        for task in tasks[:3]:
                            st.markdown(f'<div class="task-item">{task[1]}</div>', unsafe_allow_html=True)
                        if len(tasks) > 3:
                            with st.popover(f"+ {len(tasks)-3} weitere anzeigen"):
                                for task in tasks[3:]:
                                    st.markdown(f'<div class="task-item">{task[1]}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Fortschritt
                    event_stats = load_stats(st.session_state["user_id"], event_id)
                    if event_stats:
                        last_score = event_stats[0][1]
                        status, _ = calculate_progress_status(last_score)
                        
                        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                        st.markdown('<div class="progress-label">Letzte Bewertung</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="progress-score">{last_score}%</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="progress-label">{status}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Buttons
                    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
                    if st.button("Quiz", key=f"quiz_{event_id}"):
                        st.session_state.update({
                            "selected_event_id": event_id,
                            "selected_event_title": title,
                            "main_navigation": "Rätsel"
                        })
                        st.rerun()
                    if st.button("Details", key=f"details_{event_id}"):
                        st.session_state.update({
                            "selected_event_id": event_id,
                            "main_navigation": "Events"
                        })
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Ende event-card
                
                st.markdown('</div>', unsafe_allow_html=True)  # Ende event-grid
                
                # Pagination
                if total_pages > 1:
                    st.markdown('<div class="pagination-controls">', unsafe_allow_html=True)
                    st.write(f"Seite {page_number} von {total_pages}")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Noch keine Events erstellt. Erstelle dein erstes Event!")
            
            st.markdown('</div>', unsafe_allow_html=True)  # Ende stats-card

        # Geteilte Events
        shared_events = load_shared_events(st.session_state["user_id"])
        if shared_events:
            with st.container():
                st.markdown('<div class="stats-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🤝 Geteilte Events</div>', unsafe_allow_html=True)
                
                # Pagination
                items_per_page = 2  # Show fewer items per page so each has more detail
                total_pages = (len(shared_events) + items_per_page - 1) // items_per_page
                page_number = st.number_input('Seite', min_value=1, max_value=total_pages, value=1, key='shared_events_page')
                start_idx = (page_number - 1) * items_per_page
                end_idx = start_idx + items_per_page
                
                # Events Grid
                st.markdown('<div class="event-grid">', unsafe_allow_html=True)
                for event in shared_events[start_idx:end_idx]:
                    event_id, title, shared_by, description = event[0], event[1], event[2], event[3]
                    
                    st.markdown('<div class="event-card shared-event-card">', unsafe_allow_html=True)
                    
                    # Event Header with sharing info
                    st.markdown('<div class="event-header">', unsafe_allow_html=True)
                    st.markdown(f'<div class="event-name">{title}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Sharing info with timestamp (you'll need to modify your database to store this)
                    st.markdown(f'<div style="font-size:0.8rem; color:#666; margin-bottom:0.8rem;">📤 Geteilt von <b>{shared_by}</b></div>', unsafe_allow_html=True)
                    
                    # Beschreibung
                    if description:
                        with st.expander("Beschreibung anzeigen"):
                            st.write(description)
                    
                    # Aufgaben 
                    tasks = load_tasks(event_id)
                    shared_tasks = load_shared_tasks(st.session_state["user_id"])
                    all_tasks = [t for t in tasks if t[0] in [st[0] for st in shared_tasks]]
                    
                    if all_tasks:
                        st.markdown('<div class="section-label">Aufgaben</div>', unsafe_allow_html=True)
                        st.markdown('<div class="task-list">', unsafe_allow_html=True)
                        for task in all_tasks[:3]:
                            task_id, task_title = task[0], task[1]
                            with st.expander(f"✓ {task_title}"):
                                st.write(task[2])  # Task content
                                
                                # Add edit button for each task
                                if st.button(f"✏️ Bearbeiten", key=f"edit_shared_task_{task_id}"):
                                    st.session_state.update({
                                        "edit_task_id": task_id,
                                        "main_navigation": "Tasks"
                                    })
                                    st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Fortschritt
                    event_stats = load_stats(st.session_state["user_id"], event_id)
                    if event_stats:
                        last_score = event_stats[0][1]
                        status, color = calculate_progress_status(last_score)
                        
                        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                        st.markdown('<div class="progress-label">Letzte Bewertung</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="progress-score" style="color:{color}">{last_score}%</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="progress-label">{status}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Action Buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🧩 Quiz starten", key=f"shared_quiz_{event_id}"):
                            st.session_state.update({
                                "selected_event_id": event_id,
                                "selected_event_title": title,
                                "main_navigation": "Rätsel"
                            })
                            st.rerun()
                    with col2:
                        if st.button("📊 Statistik", key=f"shared_stats_{event_id}"):
                            st.session_state.update({
                                "selected_event_id": event_id,
                                "main_navigation": "Statistiken"
                            })
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Ende event-card
                
                st.markdown('</div>', unsafe_allow_html=True)  # Ende event-grid
                
                # Pagination
                if total_pages > 1:
                    st.markdown('<div class="pagination-controls">', unsafe_allow_html=True)
                    st.write(f"Seite {page_number} von {total_pages}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True) 
                
                # Pagination Controls
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    st.write(f"Seite {page_number} von {total_pages}")
                
                st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Events":
        display_page_header("Events")
        with st.container():
            st.write("### Erstelle oder bearbeite Events")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("#### Erstellte Events")
                events = load_events(st.session_state["user_id"])
                
                # Event-Auswahl und Bearbeiten/Löschen
                if events:
                    selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="event_selection")
                    selected_event_id = next(event[0] for event in events if event[1] == selected_event)
                    
                    
                    st.markdown("""
                    <style>
                    .event-action-btn {
                        min-width: 135px !important;
                        width: 100% !important;
                        background: #4A90E2 !important;
                        color: white !important;
                        border: none !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        if st.button("✏️ Bearbeiten", key="edit_event_button", 
                                help="Ausgewähltes Event bearbeiten",
                                use_container_width=True):
                            st.session_state["edit_event_id"] = selected_event_id
                            st.rerun()
                    
                    with col1_2:
                        if st.button("🗑️ Löschen", key="delete_event_button",
                                help="Ausgewähltes Event löschen",
                                use_container_width=True):
                            delete_event(selected_event_id)
                            st.success("Event erfolgreich gelöscht!")
                            # Session State bereinigen
                            if "edit_event_id" in st.session_state:
                                del st.session_state["edit_event_id"]
                            st.rerun()

                shared_events = load_shared_events(st.session_state["user_id"])
                if shared_events:
                    st.write("### Geteilte Events")
                    for event in shared_events:
                        st.write(f"**Event:** {event[1]} (Geteilt von {event[2]})")

            with col2:
                st.write("#### Event erstellen/bearbeiten")
                if "edit_event_id" in st.session_state:
                    event_to_edit = next(event for event in events if event[0] == st.session_state["edit_event_id"])
                    title = st.text_input("Titel", value=event_to_edit[1], key="edit_title")
                    description = st.text_area("Beschreibung", value=event_to_edit[2], key="edit_description")
                else:
                    title = st.text_input("Titel", key="new_title")
                    description = st.text_area("Beschreibung", key="new_description")

                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    if st.button("Speichern", key="save_event_button"):
                        if "edit_event_id" in st.session_state:
                            edit_event(st.session_state["edit_event_id"], title, description)
                            st.success("Event erfolgreich bearbeitet!")
                            del st.session_state["edit_event_id"]
                        else:
                            create_event(st.session_state["user_id"], title, description)
                            st.success("Event erfolgreich erstellt!")
                        st.rerun()
                with col2_2:
                    if st.button("Abbrechen", key="cancel_event_button"):
                        if "edit_event_id" in st.session_state:
                            del st.session_state["edit_event_id"]
                        st.rerun()

                st.write("#### Event teilen")
                all_users = load_all_users()
                if all_users and events:
                    shared_with_username = st.selectbox(
                        f"Event mit Benutzer teilen",
                        [user for user in all_users if user != st.session_state["username"]],
                        key=f"share_event_{selected_event_id}"
                    )
                    if st.button(f"Event {selected_event} teilen", key=f"share_button_{selected_event_id}"):
                        share_event(selected_event_id, st.session_state["user_id"], shared_with_username)

    elif page == "Export":
        display_page_header("Export")
        
        st.markdown("""
        <style>
        .export-container {
            max-width: 900px;
            margin: 0 auto;
        }
        .export-card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            border-left: 5px solid #4A90E2;
        }
        .export-options {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin: 1rem 0;
        }
        .download-button {
            display: inline-block; 
            background-color: #4CAF50;
            color: white !important;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 600;
            text-align: center;
            transition: background-color 0.3s;
        }
        .download-button:hover {
            background-color: #45a049;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="export-container">', unsafe_allow_html=True)
        st.markdown('<div class="export-card">', unsafe_allow_html=True)
        
        st.markdown("### 📤 Events und Aufgaben exportieren")
        st.write("Wähle die Events aus, die du exportieren möchtest, und das gewünschte Format.")
        
        # Get all events (personal and shared)
        personal_events = load_events(st.session_state["user_id"]) or []
        shared_events = load_shared_events(st.session_state["user_id"]) or []
        
        all_events = [(e[0], e[1], "Persönlich", e[2]) for e in personal_events]
        all_events += [(e[0], e[1], f"Geteilt von {e[2]}", e[3]) for e in shared_events]
        
        # Let user select which events to export
        if all_events:
            event_options = [f"{e[1]} ({e[2]})" for e in all_events]
            selected_events = st.multiselect(
                "Wähle Events zum Exportieren", 
                options=event_options,
                default=event_options
            )
            
            # Filter events based on selection
            selected_event_ids = [all_events[event_options.index(e)][0] for e in selected_events]
            
            # Export options
            export_format = st.radio(
                "Exportformat auswählen",
                ["CSV", "Excel"],
                horizontal=True
            )
            
            include_stats = st.checkbox("Statistiken einbeziehen", value=True)
            include_tasks = st.checkbox("Aufgaben einbeziehen", value=True)
            
            if st.button("Export vorbereiten"):
                if not selected_event_ids:
                    st.warning("Bitte wähle mindestens ein Event zum Exportieren aus.")
                else:
                    # Prepare data for export
                    export_data = []
                    
                    for event_id in selected_event_ids:
                        # Get event details
                        event = next((e for e in all_events if e[0] == event_id), None)
                        if not event:
                            continue
                            
                        event_id, event_title, event_type, event_desc = event
                        
                        # Get tasks
                        tasks = load_tasks(event_id) if include_tasks else []
                        
                        # Get stats
                        stats = load_stats(st.session_state["user_id"], event_id) if include_stats else []
                        
                        # Base event data
                        event_data = {
                            "Event ID": event_id,
                            "Titel": event_title,
                            "Typ": event_type,
                            "Beschreibung": event_desc
                        }
                        
                        if not tasks:
                            # Just add the event without tasks
                            export_data.append(event_data)
                        else:
                            # Add each task as a separate row
                            for task in tasks:
                                task_id, task_title, task_content = task[0], task[1], task[2]
                                
                                task_data = event_data.copy()
                                task_data.update({
                                    "Aufgabe ID": task_id,
                                    "Aufgabe Titel": task_title,
                                    "Aufgabe Inhalt": task_content
                                })
                                
                                # Add stats if available
                                if include_stats:
                                    task_stats = [s for s in stats if s[2] == task_id]
                                    if task_stats:
                                        latest_stat = task_stats[-1]
                                        task_data.update({
                                            "Letzte Bewertung": latest_stat[1],
                                            "Datum": latest_stat[3] if len(latest_stat) > 3 else "Unbekannt"
                                        })
                                
                                export_data.append(task_data)
                    
                    # Create DataFrame
                    df = pd.DataFrame(export_data)
                    
                    # Create download link
                    if export_format == "CSV":
                        filename = "events_export.csv"
                        st.markdown(create_download_link(df, filename, "📥 CSV-Datei herunterladen"), unsafe_allow_html=True)
                    else:  # Excel
                        # For Excel, we need to use BytesIO
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name='Events', index=False)
                        
                        b64 = base64.b64encode(output.getvalue()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="events_export.xlsx" class="download-button">📥 Excel-Datei herunterladen</a>'
                        st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("Keine Events zum Exportieren vorhanden. Erstelle zuerst Events oder nehme an geteilten Events teil.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Tasks":
        display_page_header("Tasks")
        with st.container():
            st.write("### Erstelle oder bearbeite Tasks")
            events = load_events(st.session_state["user_id"])
            if events:
                selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="task_event_selection")
                selected_event_id = next(event[0] for event in events if event[1] == selected_event)
                tasks = load_tasks(selected_event_id)
                shared_tasks = load_shared_tasks(st.session_state["user_id"])
                all_tasks = tasks + shared_tasks

                if all_tasks:
                    selected_task = st.selectbox("Wähle eine Aufgabe", [task[1] for task in all_tasks], key="task_selection")
                    selected_task_id = next(task[0] for task in all_tasks if task[1] == selected_task)
                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        if st.button("✏️ Bearbeiten", key="edit_task_button"):
                            st.session_state["edit_task_id"] = selected_task_id
                    with col1_2:
                        if st.button("🗑️ Löschen", key="delete_task_button"):
                            delete_task(selected_task_id)
                            st.rerun()

                st.write("#### Task erstellen/bearbeiten")
                if "edit_task_id" in st.session_state:
                    task_to_edit = next(task for task in all_tasks if task[0] == st.session_state["edit_task_id"])
                    title = st.text_input("Titel", value=task_to_edit[1], key="edit_task_title")
                    content = st.text_area("Inhalt", value=task_to_edit[2], key="edit_task_content")
                else:
                    title = st.text_input("Titel", key="new_task_title")
                    content = st.text_area("Inhalt", key="new_task_content")

                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    if st.button("Speichern", key="save_task_button"):
                        if "edit_task_id" in st.session_state:
                            edit_task(st.session_state["edit_task_id"], title, content)
                            del st.session_state["edit_task_id"]
                        else:
                            save_task(selected_event_id, title, content)
                        st.rerun()
                with col2_2:
                    if st.button("Abbrechen", key="cancel_task_button"):
                        if "edit_task_id" in st.session_state:
                            del st.session_state["edit_task_id"]
                        st.rerun()

    elif page == "Rätsel":
        events = load_events(st.session_state["user_id"])
        if events:
            selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="quiz_event_selection")
            selected_event_id = next(event[0] for event in events if event[1] == selected_event)
            quiz_mode(st.session_state["user_id"], selected_event_id)
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Statistiken":
        display_page_header("Statistiken")
        events = load_events(st.session_state["user_id"])
        if events:
            selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="stats_event_selection")
            selected_event_id = next(event[0] for event in events if event[1] == selected_event)
            display_event_statistics(st.session_state["user_id"], selected_event_id)
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Profil":
        display_page_header("Profil")
        st.write(f"Eingeloggt als: {st.session_state['username']}")
        if st.button("Ausloggen", key="logout_button"):
            logout()

    elif page == "Einstellungen":
        display_page_header("Einstellungen")
        st.write("Konfiguriere die Anwendungseinstellungen.")

        dark_mode = st.checkbox(
            "Dunkelmodus aktivieren",
            value=st.session_state["dark_mode"],
            key="dark_mode_checkbox"
        )
        if dark_mode != st.session_state["dark_mode"]:
            st.session_state["dark_mode"] = dark_mode
            st.rerun()

    elif page == "Über die Anwendung":
        
        # Custom CSS für diesen Abschnitt
        st.markdown("""
        <style>
        .feature-card {
            background-color: #F8FAFF;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #E0E7FF;
        }
        .tip-card {
            background-color: #FFF8E6;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #FFA500;
        }
        .step-card {
            background-color: #F0F9FF;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0;
        }
        .api-card {
            background-color: #F5F5F5;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            
            
            st.markdown("""
            <h2 style='color: #4A90E2; border-bottom: 2px solid #4A90E2; padding-bottom: 0.5rem;'>
            🚀 EventManager – Dein Assistent für die Eventplanung
            </h2>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
            <h3 style='color: #4A90E2;'>✨ Hauptfunktionen</h3>
            <ul style='margin-left: 1.5rem;'>
                <li><b>Events erstellen und verwalten</b> - Behalte alle deine Veranstaltungen im Überblick</li>
                <li><b>Aufgaben (Tasks) für Events hinzufügen</b> - Organisiere deine To-Dos effizient</li>
                <li><b>Fragen basierend auf den Aufgaben generieren</b> - Teste dein Wissen mit KI-generierten Quizzen</li>
                <li><b>Fortschritte verfolgen</b> - Analysiere deine Leistung mit detaillierten Statistiken</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='margin: 2rem 0;'>
            <h3 style='color: #4A90E2;'>🔧 Wie funktioniert es?</h3>
            """, unsafe_allow_html=True)
            
            steps = [
                ("1. **Events erstellen**", "Gib deine Events ein (z.B. 'Hochzeit', 'Geburtstagsfeier')"),
                ("2. **Aufgaben hinzufügen**", "Füge Tasks wie 'Location buchen' oder 'Catering bestellen' hinzu"),
                ("3. **Rätsel-Modus**", "Beantworte KI-generierte Fragen zu deinen Tasks"),
                ("4. **Statistiken**", "Verfolge deine Quiz-Ergebnisse und verbessere dich")
            ]
            
            for step, desc in steps:
                st.markdown(f"""
                <div class="step-card">
                    <h4 style='margin: 0; color: #4A90E2;'>{step}</h4>
                    <p style='margin: 0.5rem 0 0 0;'>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="tip-card">
            <h3 style='color: #FFA500;'>💡 Tipps für perfekte Quiz-Antworten</h3>
            <table style='width: 100%; border-collapse: collapse; margin-top: 0.5rem;'>
                <tr>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3; vertical-align: top;'>
                        <b>📊 Quantitative Angaben</b>
                    </td>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3;'>
                        Verwende konkrete Zahlen, Daten und Prozentwerte
                    </td>
                </tr>
                <tr>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3; vertical-align: top;'>
                        <b>⏱️ Prozessschritte</b>
                    </td>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3;'>
                        Nenne Zeitangaben und Meilensteine
                    </td>
                </tr>
                <tr>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3; vertical-align: top;'>
                        <b>📝 Kriterien</b>
                    </td>
                    <td style='padding: 0.5rem; border-bottom: 1px solid #FFE8B3;'>
                        Begründe Entscheidungen mit nachvollziehbaren Bewertungen
                    </td>
                </tr>
                <tr>
                    <td style='padding: 0.5rem; vertical-align: top;'>
                        <b>🗂️ Struktur</b>
                    </td>
                    <td style='padding: 0.5rem;'>
                        Gliedere Antworten klar (z.B. nummerierte Listen)
                    </td>
                </tr>
            </table>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="api-card">
            <h3 style='color: #4A90E2;'>🔑 DeepSeek API-Key</h3>
            <p>Um Fragen zu generieren, benötigst du einen DeepSeek API-Key:</p>
            <ol>
                <li>Erstelle ein kostenloses Konto auf <a href="https://openrouter.ai" target="_blank">OpenRouter</a></li>
                <li>Generiere einen API-Key für DeepSeek</li>
                <li>Trage den Key in den <a href="/#api-key-konfigurieren">Einstellungen</a> ein</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
