import datetime
import logging
import requests
import streamlit as st
from dotenv import load_dotenv
from utils.mascot_reactions import show_mascot_reaction
from utils.auth import register, login, logout, load_all_users, update_profile, TEXT_COLOR, get_user_premium_status_and_quiz_limits
from utils.event_manager import create_event, edit_event, delete_event, load_events, load_shared_events, load_tasks, share_event
from utils.task_manager import save_task, edit_task, delete_task, load_shared_tasks
from utils.event_question_generator import chat_with_deepseek, quiz_mode, DAILY_QUIZ_LIMIT_FREE
from utils.event_stats_manager import calculate_progress_status, load_stats, display_event_statistics
import os
import pandas as pd
import io
import base64
from utils.database import create_connection, create_tables
from streamlit_cookies_manager import EncryptedCookieManager


# Design-Konstanten
PRIMARY_COLOR = "#4A90E2"
SECONDARY_COLOR = "#F5F5F5"
ACCENT_COLOR = "#FFA500"
DARK_BG = "#1E1E1E"
DARK_CARD = "#2D2D2D"

# Schlüssel für sichere Cookie-Speicherung (ändern für echte Sicherheit!)
cookies = EncryptedCookieManager(
    prefix="eventmanager_", password="test"
)
if not cookies.ready():
    st.stop()

if "cookies" not in st.session_state:
    st.session_state["cookies"] = cookies  

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = cookies.get("dark_mode", "false") == "true"

# === CSS Global Definition ===
# Wir definieren die CSS-Variablen und globalen Styles hier,
# damit sie immer verfügbar sind.
# Die Dark-Mode-Styles überschreiben die Light-Mode-Styles später,
# wenn die 'dark-mode'-Klasse gesetzt ist.

MAIN_CSS = f"""
<style>
/* CSS Variablen Definitionen - Zugänglich für alle Styles */
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

/* Globale Styles (Standard / Hellmodus) */
.stApp {{
    background-color: var(--secondary); /* Hellmodus Hintergrund */
    color: {TEXT_COLOR}; /* Hellmodus Textfarbe */
    line-height: 1.6;
}}

/* Sidebar - Standard (Hellmodus) */
/* Diese Regel gilt jetzt explizit nur für den Hellmodus, da der Dark Mode sie überschreiben wird */
[data-testid="stSidebar"] {{
    background: linear-gradient(135deg, var(--primary), #6a11cb); /* Dein Hellmodus-Gradient */
}}

/* Sidebar Radio Buttons - Standard (Hellmodus) */
[data-testid="stSidebar"] .stRadio label {{
    color: white !important; /* Weiß für den Gradient-Hintergrund */
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

/* Fix headers */
header, #MainMenu, div[data-testid="stStatusWidget"], div[data-testid="stToolbar"] {{
    display: none !important;
}}

/* Cards - Standard (Hellmodus) */
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

/* Buttons - Standard (Hellmodus) */
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

/* Task Items - Standard (Hellmodus) */
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

/* Hide Streamlit's default header/footer */
body > div:first-child {{
    visibility: hidden;
}}

/* Footer Styles (Standard / Hellmodus) */
/* Footer im Dark Mode */
             /* Footer Styling - Fixed position */
            .footer-container {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: {'#2D2D2D' if st.session_state.dark_mode else '#F0F2F6'}; /* Use a neutral background, or dark/light mode specific */
                text-align: center;
                padding: 1rem 0;
                border-top: 2px solid {'#3A3A3A' if st.session_state.dark_mode else '#e0e0e0'};
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
                z-index: 9999; /* Ensure it stays on top */
            }}

            .footer {{
                color: {'#BBBBBB' if st.session_state.dark_mode else '#555'};
                font-size: 0.9rem;
            }}
            .footer a {{
                color: {'#7ABFFF' if st.session_state.dark_mode else '#4A90E2'};
                text-decoration: none;
                font-weight: bold;
                margin: 0 0.5rem;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
            .footer-icon {{
                margin-right: 4px;
                vertical-align: middle;
            }}

/* API Card Styles (Standard / Hellmodus) */
.api-card {{
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-left: 4px solid var(--accent);
    transition: var(--transition);
}}
.api-card h3 {{
    color: var(--primary);
}}
.api-card a {{
    color: var(--primary); /* Standard-Linkfarbe für API-Karten */
}}

</style>
"""

# Füge MAIN_CSS am Anfang deiner App ein, bevor andere UI-Elemente gerendert werden
st.markdown(MAIN_CSS, unsafe_allow_html=True)


# === Dark Mode Overrides and JS Injection ===
# Dieser Block wird NACH MAIN_CSS geladen. Die Regeln hier überschreiben die Standardwerte
# NUR WENN der Dunkelmodus aktiv ist.
if st.session_state.dark_mode:
    st.markdown(f"""
        <style>
            /* Allgemeine Dark Mode Overrides */
            .stApp {{
                background-color: var(--dark-bg) !important;
                color: white !important;
            }}
            
            /* Sidebar im Dark Mode (Priorität durch .dark-mode body) */
            /* Wichtig: Hier setzen wir den Hintergrund direkt auf --dark-card */
            [data-testid="stSidebar"] {{
                background: var(--dark-card) !important; /* Hellt Schwarz für Sidebar */
            }}
            
            /* Sidebar Radio Buttons im Dark Mode */
            [data-testid="stSidebar"] .stRadio label {{
                color: white !important;
            }}
            [data-testid="stSidebar"] .stRadio label:hover {{
                background: rgba(255, 255, 255, 0.1) !important;
            }}
            [data-testid="stSidebar"] .stRadio [aria-checked="true"] + label {{
                background: rgba(255, 255, 255, 0.2) !important;
                font-weight: 600 !important;
            }}

            /* Cards im Dark Mode */
            .card {{
                background-color: var(--dark-card) !important;
            }}

            .shared-card {{
                border-left: 4px solid var(--accent) !important; /* Behalte Akzentfarbe */
            }}

            /* Task Items im Dark Mode */
            .task-item {{
                background: #2a3d5c !important;
            }}
            
            /* Buttons im Dark Mode (falls spezifische Anpassungen gewünscht) */
            .stButton>button {{
                background-color: var(--primary) !important;
                color: white !important;
            }}
            .stButton>button:hover {{
                background-color: #3a7bc8 !important;
            }}

            /* Auth Form Container im Dark Mode */
            .auth-form-container {{
                background-color: var(--dark-card) !important;
                color: white !important;
                border-top: 5px solid var(--primary) !important;
            }}
            .auth-form-title {{
                color: white !important;
            }}
            .stTextInput>div>div>input, .stSelectbox>div>div {{
                background-color: #3A3A3A !important;
                color: #F5F5F5 !important;
                border: 1px solid #555 !important;
            }}
            .stTextInput label, .stSelectbox label {{
                color: #F5F5F5 !important;
            }}
            
            /* Markdown für API Key Card im Dark Mode */
            .api-card {{
                background-color: var(--dark-card) !important;
                color: white !important;
                border-left-color: var(--accent) !important;
            }}
            .api-card h3 {{
                color: var(--primary) !important;
            }}
            .api-card a {{
                color: var(--accent) !important; /* Akzentfarbe für Links im Dark Mode */
            }}

            /* Footer im Dark Mode */
            .footer {{
                color: white !important;
                border-top-color: #444 !important;
            }}
            .footer a {{
                color: var(--accent) !important; /* Akzentfarbe für Links im Dark Mode */
            }}
        </style>
        <script>
            // Fügt die 'dark-mode' Klasse zum body Element des übergeordneten Dokuments hinzu
            const body = window.parent.document.querySelector('body');
            if (body) {{
                body.classList.add('dark-mode');
            }}
        </script>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            /* Dieser leere Style-Block ist wichtig, um den JS-Block auszuführen, wenn Dark Mode aus ist. */
        </style>
        <script>
            // Entfernt die 'dark-mode' Klasse vom body Element des übergeordneten Dokuments
            const body = window.parent.document.querySelector('body');
            if (body) {{
                body.classList.remove('dark-mode');
            }}
        </script>
    """, unsafe_allow_html=True)

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

base64_img = get_base64_image("data/assets/icons/mascott.png")

st.markdown(f"""
<style>
@keyframes wobble {{
  0%, 100% {{ transform: translateY(0px); }}
  50% {{ transform: translateY(10px); }}
}}

#mascot {{
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 350px;
  animation: wobble 3s infinite ease-in-out;
  pointer-events: none;
  z-index: 1001;
}}
</style>

<img id="mascot" src="data:image/png;base64,{base64_img}" />
""", unsafe_allow_html=True)




# database initialization
if not os.path.exists("data"):
    os.makedirs("data")

# creation of tables
try:
    create_tables()
except Exception as e:
    st.error(f"error while initializing the database: {e}")

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

API_URL = "http://localhost:8000"

def get_chat_history(user_id, event_id=None, task_id=None):
    params = {"user_id": user_id}
    if event_id: params["event_id"] = event_id
    if task_id: params["task_id"] = task_id
    resp = requests.get(f"{API_URL}/chat/history", params=params)
    try:
        return resp.json()
    except Exception:
        st.error(f"Fehler beim Laden des Chatverlaufs: {resp.status_code} - {resp.text}")
        return []

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


# Helper function to clear chat history (you'll need to implement this)
def clear_chat_history(user_id, event_id, task_id=None):
        params = {"user_id": user_id, "event_id": event_id}
        if task_id:
            params["task_id"] = task_id
        
        try:
            resp = requests.delete(f"{API_URL}/chat/history", params=params)
            return resp.status_code == 200
        except:
            return False


# Hilfsfunktion für bessere Chat-Historie Anzeige
def get_chat_history(user_id, event_id=None, task_id=None):
    """
    Optimierte Funktion zum Laden der Chat-Historie mit besserer Fehlerbehandlung.
    """
    try:
        response = requests.get(f"{API_URL}/chat/history", params={
            "user_id": user_id,
            "event_id": event_id,
            "task_id": task_id
        }, timeout=10)  # Timeout hinzufügen
        
        if response.status_code == 200:
            history = response.json()
            return history if isinstance(history, list) else []
        else:
            logging.error(f"Chat-Historie API Fehler: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Netzwerk-Fehler beim Laden der Chat-Historie: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unerwarteter Fehler beim Laden der Chat-Historie: {str(e)}")
        return [] 

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
    "Chat": "💬"
}

BACKGROUND_CSS = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-size: cover;
    background-attachment: fixed;
}}

.auth-bg {{
    background-size: cover;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}}
</style>
"""

DARK_MODE_CSS = f"""
<style>
    :root {{
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
        --dark-text: #E0E0E0;
        --dark-border: #333333;
        --dark-accent: {ACCENT_COLOR};
    }}

    /* Globale Hintergründe */
    .dark-mode [data-testid="stAppViewContainer"] {{
        background-color: var(--dark-bg) !important;
        color: var(--dark-text) !important;
    }}

    /* Sidebar */
    .dark-mode [data-testid="stSidebar"] {{
        background: linear-gradient(135deg, #1a1a1a, #2a2a2a) !important;
    }}

    /* Karten & Container */
    .dark-mode .card, 
    .dark-mode .stats-card,
    .dark-mode .export-card {{
        background-color: var(--dark-card) !important;
        border-left: 4px solid var(--dark-accent) !important;
        color: var(--dark-text) !important;
    }}

    /* Text & Überschriften */
    .dark-mode .stMarkdown h1,
    .dark-mode .stMarkdown h2,
    .dark-mode .stMarkdown h3,
    .dark-mode .stMarkdown p {{
        color: var(--dark-text) !important;
    }}

    /* Formularelemente */
    .dark-mode .stTextInput input,
    .dark-mode .stTextArea textarea,
    .dark-mode .stSelectbox select {{
        background-color: #2a2a2a !important;
        color: var(--dark-text) !important;
        border-color: var(--dark-border) !important;
    }}

    /* Tabellen */
    .dark-mode .stDataFrame {{
        background-color: var(--dark-card) !important;
    }}

    /* Spezielle Komponenten (wie in deinem Screenshot) */
    .dark-mode .checkbox-label {{
        color: var(--dark-text) !important;
    }}

    .dark-mode .stCheckbox label {{
    color: var(--dark-text) !important;
}}
    .dark-mode .stMarkdown ul {{
        color: var(--dark-text) !important;
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


st.markdown("""
    <script>
        setTimeout(() => {
            document.querySelector('body > div:first-child').style.visibility = 'visible';
        }, 100);
    </script>
""", unsafe_allow_html=True)

FULL_WIDTH_CSS = """
<style>
/* Nutze gesamte Breite für Container */
.dashboard-container, .stats-card, .event-card, .main-content {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 1rem 2rem !important;
    box-sizing: border-box;
}

/* Grid-Layout für Events */
.event-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
}

/* Responsive Anpassung */
@media screen and (max-width: 768px) {
    .event-grid {
        grid-template-columns: 1fr;
    }
}

/* Optional: Container optisch abtrennen */
.divider {
    height: 1px;
    background: linear-gradient(to right, transparent, var(--primary), transparent);
    margin: 2rem 0;
    border: none;
}

/* Wenn Sidebar versteckt ist */
.sidebar-hidden [data-testid="stSidebar"] {
    display: none !important;
}
.sidebar-hidden .block-container {
    padding-left: 2rem !important;
}
</style>
"""



st.markdown(MAIN_CSS + LOGIN_CSS, unsafe_allow_html=True)
if st.session_state.dark_mode:
    st.markdown(
        f"""
        <style>
        /* Allgemeine Hintergrundfarbe und Textfarbe für den Dunkelmodus */
        body {{
            background-color: #1E1E1E; /* DARK_BG aus auth.py */
            color: #F5F5F5; /* Helle Textfarbe */
        }}
        .stApp {{
            background-color: #1E1E1E; /* Für die Streamlit-App selbst */
            color: #F5F5F5;
        }}
        /* Streamlit-Container und -Elemente anpassen */
        .stSidebar {{
            background-color: #2D2D2D; /* DARK_CARD für Sidebar */
            color: #F5F5F5;
        }}
        .st-emotion-cache-1jm6jmz {{ /* Beispiel für ein st.container oder st.expander Hintergrund */
            background-color: #2D2D2D; /* DARK_CARD */
            border-radius: 10px;
            padding: 20px;
        }}
        .st-emotion-cache-1n106b3 {{ /* st.expander Header */
            background-color: #2D2D2D;
            color: #F5F5F5;
        }}
        .stButton>button {{
            background-color: #4A90E2; /* PRIMARY_COLOR */
            color: white;
        }}
        .stButton>button:hover {{
            background-color: #3A7EDA; /* Leicht dunkler beim Hover */
        }}
        /* Textfelder, Selectboxen etc. anpassen */
        .stTextInput>div>div>input, .stSelectbox>div>div {{
            background-color: #3A3A3A;
            color: #F5F5F5;
            border: 1px solid #555;
        }}
        /* Markdown-Elemente anpassen (z.B. für Code-Blöcke) */
        code {{
            background-color: #3A3A3A;
            color: #A9B7C6;
        }}
        pre {{
            background-color: #3A3A3A;
            color: #A9B7C6;
            border: 1px solid #555;
        }}
        /* Und andere spezifische Elemente, die du im Dunkelmodus ändern möchtest */
        /* Wenn du spezielle Container-Klassen hast (wie .auth-form-container aus auth.py) */
        .auth-form-container {{
            background-color: #2D2D2D !important; /* DARK_CARD */
            color: #F5F5F5 !important;
            border-top: 5px solid #4A90E2 !important; /*PRIMARY_COLOR*/
        }}

        .custom-navbar {{ /* Passe diesen Selektor an deine tatsächliche Klasse/ID an */
            background-color: #2D2D2D; /* Der gewünschte dunkle Hintergrund (DARK_CARD) */
            color: #F5F5F5; /* Helle Textfarbe für die Navigation */
            /* Weitere Styling-Optionen, z.B. für Padding, Schatten, etc. */
            padding: 10px 20px; /* Beispiel-Padding */
            box-shadow: 0 2px 5px rgba(0,0,0,0.3); /* Beispiel-Schatten */
        }}
        .custom-navbar a {{ /* Für die Links innerhalb der Navigation */
            color: #F5F5F5; /* Helle Textfarbe für Links */
            text-decoration: none;
            margin-right: 15px; /* Abstand zwischen Links */
        }}
        .custom-navbar a:hover {{
            color: #4A90E2; /* PRIMARY_COLOR für Hover-Effekt */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    # Hier die Stile für den Hellmodus (Standard)
    st.markdown(
        """
        <style>
        body {
            background-color: #FFFFFF; /* Standard-Hintergrundfarbe */
            color: #333333; /* Standard-Textfarbe */
        }
        .stApp {
            background-color: #FFFFFF;
            color: #333333;
        }
        .stSidebar {
            background-color: #F5F5F5; /* SECONDARY_COLOR */
            color: #333333;
        }
        .st-emotion-cache-1jm6jmz { /* Beispiel für ein st.container oder st.expander Hintergrund */
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 20px;
        }
        .st-emotion-cache-1n106b3 { /* st.expander Header */
            background-color: #FFFFFF;
            color: #333333;
        }
        .stButton>button {
            background-color: #4A90E2; /* PRIMARY_COLOR */
            color: white;
        }
        .stButton>button:hover {
            background-color: #3A7EDA;
        }
        .stTextInput>div>div>input, .stSelectbox>div>div {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #E0E0E0;
        }
        code {
            background-color: #E0E0E0;
            color: #333333;
        }
        pre {
            background-color: #E0E0E0;
            color: #333333;
            border: 1px solid #D0D0D0;
        }
        .auth-form-container {
            background-color: white !important;
            color: #333 !important;
            border-top: 5px solid #4A90E2 !important; /*PRIMARY_COLOR*/
        }
        </style>
        """,
        unsafe_allow_html=True
    )  

# Zustandsvariablen initialisieren mit Default-Werten
if "logged_in" not in st.session_state:
    st.session_state.logged_in = cookies.get("logged_in") == "true"
    st.session_state.user_id = cookies.get("user_id")
    st.session_state.username = cookies.get("username")
    if "is_premium" not in st.session_state:
        st.session_state.is_premium = cookies.get("is_premium", "0") == "1"

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
        available_pages = ["Dashboard", "Events", "Tasks", "Rätsel", "Statistiken", "Profil", "Einstellungen","Export", "Über die Anwendung", "Chat"]
        
        
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
                        show_mascot_reaction("success", "API-Key erfolgreich gespeichert!")
                        load_dotenv(override=True)
                    else:
                        st.error("Bitte gib einen gültigen API-Key ein.")

elif not st.session_state["logged_in"]:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa !important;
        background-size: cover;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("show_login", True):
        login(cookies)
    else:
        register()

else:
    if page == "Dashboard":
        display_page_header("Dashboard")
        # NEU: Anzeige des Premium-Status und Quiz-Limits
        is_premium_user, daily_quiz_count, _ = get_user_premium_status_and_quiz_limits(st.session_state.user_id)
        
        st.markdown("<br>", unsafe_allow_html=True) # Abstand
        
        col_premium, col_quiz_limit = st.columns([1, 1])
        
        with col_premium:
            if is_premium_user:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #D4EDDA; 
                        padding: 10px; 
                        border-radius: 8px; 
                        border: 1px solid #28A745; 
                        text-align: center;
                        color: #155724;
                    ">
                        ✨ Du bist ein <b>Premium-Nutzer</b>! Genieße unbegrenzte Funktionen.
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #FFF3CD; 
                        padding: 10px; 
                        border-radius: 8px; 
                        border: 1px solid #FFC107; 
                        text-align: center;
                        color: #856404;
                    ">
                        🚀 Du bist ein <b>Free-Nutzer</b>. Upgrade jetzt auf Premium!
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        with col_quiz_limit:
            if not is_premium_user:
                remaining_quizzes = DAILY_QUIZ_LIMIT_FREE - daily_quiz_count
                if remaining_quizzes < 0: remaining_quizzes = 0 # Sollte nicht passieren, aber zur Sicherheit
                st.markdown(
                    f"""
                    <div style="
                        background-color: #E0F7FA; 
                        padding: 10px; 
                        border-radius: 8px; 
                        border: 1px solid #00BCD4; 
                        text-align: center;
                        color: #006064;
                    ">
                        📚 Verbleibende Quizfragen heute: <b>{remaining_quizzes}</b>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #D4EDDA; 
                        padding: 10px; 
                        border-radius: 8px; 
                        border: 1px solid #28A745; 
                        text-align: center;
                        color: #155724;
                    ">
                        ✅ Unbegrenzte Quizfragen als Premium-Nutzer!
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True) # Abstand
        
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
        .imported-event-card {
            border-left: 3px solid #E24A90 !important;
        }
        .imported-badge {
            background-color: #F8E6F5 !important;
            color: #E24A90 !important;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-left: 0.5rem;
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
            display: flex;
            align-items: center;
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
            color: #333 !important;
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
            
            cols = st.columns(3)
            num_events = len(events) if events else 0
            num_quizzes = len(stats) if stats else 0
            avg_score = sum(stat[1] for stat in stats)/num_quizzes if num_quizzes > 0 else 0
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
                # Filter für importierte/nicht importierte Events
                show_imported = st.checkbox("Importierte Events anzeigen", value=True, key="show_imported_checkbox")
                filtered_events = [e for e in events if show_imported or (len(e) > 3 and not e[3])]
                
                if filtered_events:  # Nur anzeigen wenn gefilterte Events vorhanden sind
                    # Pagination
                    items_per_page = 2
                    total_pages = max(1, (len(filtered_events) + items_per_page - 1) // items_per_page)
                    page_number = st.number_input('Seite', min_value=1, max_value=total_pages, value=1, key='events_page')
                    start_idx = (page_number - 1) * items_per_page
                    end_idx = start_idx + items_per_page
                    
                    # Events Grid
                    st.markdown('<div class="event-grid">', unsafe_allow_html=True)
                    for event in filtered_events[start_idx:end_idx]:
                        event_id, title, description = event[0], event[1], event[2]
                        is_imported = len(event) > 3 and event[3]  # Index 3 = is_imported
                        
                        st.markdown(f'<div class="event-card {"imported-event-card" if is_imported else ""}">', unsafe_allow_html=True)
                        
                        # Event Header
                        st.markdown('<div class="event-header">', unsafe_allow_html=True)
                        st.markdown(f'<div class="event-name">{title}{" <span class=\"imported-badge\">importiert</span>" if is_imported else ""}</div>', unsafe_allow_html=True)
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
                    st.info("Keine Events mit den aktuellen Filtereinstellungen gefunden.")
            else:
                st.info("Noch keine Events erstellt. Erstelle dein erstes Event oder importiere welche!")
            
            st.markdown('</div>', unsafe_allow_html=True)  # Ende stats-card

        # Geteilte Events
        shared_events = load_shared_events(st.session_state["user_id"])
        if shared_events:
            with st.container():
                st.markdown('<div class="stats-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🤝 Geteilte Events</div>', unsafe_allow_html=True)
                
                # Pagination
                items_per_page = 2
                total_pages = max(1, (len(shared_events) + items_per_page - 1) // items_per_page)
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
                    
                    # Sharing info
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

    elif page == "Events":
        display_page_header("Events")
        with st.container():
            st.write("### Erstelle oder bearbeite Events")
            col1, col2 = st.columns([1,3])
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
                    /* Eingabefelder und Textbereiche */
                    input[type="text"], textarea, .stTextInput > div > div > input, .stTextArea > div > textarea {
                        border-radius: 10px !important;
                        border: 2px solid #4A90E2 !important;
                        padding: 0.5rem !important;
                    }

                    .stButton > button {
                    border-radius: 10px !important;
                    background-color: #4A90E2 !important;
                    color: white !important;
                    border: none !important;
                    padding: 0.6rem 1.2rem !important;
                    font-weight: bold !important;
                }

                .stButton > button:hover {
                    background-color: #357ABD !important;
                }
            
                                    
                                        
                
                                
                    </style>
                    """, unsafe_allow_html=True)
                    
                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        if st.button("✏️", key="edit_event_button", 
                                help="Ausgewähltes Event bearbeiten",
                                use_container_width=True):
                            st.session_state["edit_event_id"] = selected_event_id
                            st.rerun()
                    
                    with col1_2:
                        if st.button("🗑️", key="delete_event_button",
                                help="Ausgewähltes Event löschen",
                                use_container_width=True):
                            delete_event(selected_event_id)
                            st.success("Event erfolgreich gelöscht!")
                            show_mascot_reaction("success", "Event erfolgreich gelöscht!")
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
                    description = st.text_area("Beschreibung", value=event_to_edit[2], key="edit_description", height=300)
                else:
                    title = st.text_input("Titel", key="new_title")
                    description = st.text_area("Beschreibung", key="new_description",height=300)

                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    if st.button("Speichern", key="save_event_button"):
                        if "edit_event_id" in st.session_state:
                            edit_event(st.session_state["edit_event_id"], title, description)
                            st.success("Event erfolgreich bearbeitet!")
                            show_mascot_reaction("success", "Event erfolgreich bearbeitet!")
                            del st.session_state["edit_event_id"]
                            st.rerun()
                        else:
                            create_event(st.session_state["user_id"], title, description)
                            st.success("Event erfolgreich erstellt!")
                            show_mascot_reaction("success", "Event erfolgreich erstellt!")
                            st.rerun()

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


    elif page == "Chat":
        from datetime import datetime
        from utils.event_question_generator import chat_with_deepseek

        display_page_header("Chat")

        events = load_events(st.session_state["user_id"])
        if not events:
            st.info("Keine Events verfügbar.")
            show_mascot_reaction("info", "Event Keine Events verfügbar!")
            st.stop()

        tab_titles = [e[1] for e in events]
        tabs = st.tabs(tab_titles)

        if "selected_task_id" not in st.session_state:
            st.session_state.selected_task_id = None
        if "selected_event_id" not in st.session_state:
            st.session_state.selected_event_id = None

        # 📌 Styling - Nur für Chat-Seite
        st.markdown("""
        <style>
        /* Nur Performance-Optimierungen ohne Layout-Störungen */
        .stSpinner > div {
            display: none !important;
        }
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        /* Task Card Styling */
        .task-card {
            background: #fcfcfc;
            border-radius: 12px;
            padding: 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.06);
            margin-bottom: 1rem;
            height: 185px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #e8e8e8;
        }
        .task-card-content {
            padding: 1.2rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            height: calc(100% - 45px);
        }
        .task-card h4 {
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: #333;
            line-height: 1.3;
            max-height: 2.6rem;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        .task-card p {
            font-size: 0.85rem;
            color: #666;
            margin: 0;
            flex-grow: 1;
            line-height: 1.4;
            max-height: 4.2rem;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }
        .chat-top-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.2rem;
        }
        .chat-back-btn, .chat-action-btn {
            background: #fff;
            color: #4A90E2;
            border: 1.5px solid #4A90E2;
            border-radius: 8px;
            padding: 0.5rem 0.9rem;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .chat-back-btn:hover, .chat-action-btn:hover {
            background: #eaf4fb;
        }
        [data-testid="stChatInput"] textarea {
            background: #f7faff !important;
            border: 2px solid #4A90E2 !important;
            border-radius: 10px !important;
            font-size: 1.08rem !important;
            color: #222 !important;
            padding: 1.1rem !important;
            min-height: 70px !important;
            box-shadow: 0 2px 8px rgba(74,144,226,0.08);
            transition: border 0.2s;
        }
        [data-testid="stChatInput"] textarea:focus {
            border: 2px solid #357ABD !important;
            outline: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        for idx, tab in enumerate(tabs):
            with tab:
                event_id = events[idx][0]

                tasks = load_tasks(event_id)
                if not tasks:
                    st.info("Für dieses Event sind keine Aufgaben vorhanden. Bitte lege zuerst Aufgaben an, um den Chat zu nutzen.")
                    show_mascot_reaction("info", "Keine Aufgaben vorhanden!")
                    continue

                # Chat-Ansicht nur anzeigen, wenn sowohl Task als auch Event ausgewählt sind
                if (st.session_state.selected_task_id is not None and 
                    st.session_state.selected_event_id == event_id):
                    
                    task = next((t for t in tasks if t[0] == st.session_state.selected_task_id), None)
                    if not task:
                        st.warning("Aufgabe nicht gefunden.")
                        st.session_state.selected_task_id = None
                        st.session_state.selected_event_id = None
                        st.rerun()

                    # 🔝 Chat Top Bar mit Symbolbuttons
                    st.markdown('<div class="chat-top-bar">', unsafe_allow_html=True)
                    col_back, col_title, col_actions = st.columns([1, 6, 3])
                    with col_back:
                        if st.button("⬅️", key=f"back_to_tasks_{event_id}_{st.session_state.selected_task_id}", 
                                   help="Zurück zur Aufgabenliste", use_container_width=True):
                            st.session_state.selected_task_id = None
                            st.session_state.selected_event_id = None
                            st.rerun()
                    with col_title:
                        st.markdown(f"<h4 style='margin-bottom:0;'>{task[1]}</h4>", unsafe_allow_html=True)
                    with col_actions:
                        chat_history = get_chat_history(
                            user_id=st.session_state["user_id"],
                            event_id=st.session_state.selected_event_id,
                            task_id=st.session_state.selected_task_id
                        )
                        if chat_history:
                            import pandas as pd
                            import base64
                            df = pd.DataFrame(chat_history)
                            csv = df.to_csv(index=False)
                            b64 = base64.b64encode(csv.encode()).decode()
                            href = f'<a href="data:file/csv;base64,{b64}" download="chat_export.csv" class="chat-action-btn">💾</a>'
                            st.markdown(href, unsafe_allow_html=True)

                        if st.button("🗑️", key=f"clear_chat_btn_{event_id}_{st.session_state.selected_task_id}", 
                                   help="Chatverlauf löschen"):
                            if clear_chat_history(
                                user_id=st.session_state["user_id"],
                                event_id=st.session_state.selected_event_id,
                                task_id=st.session_state.selected_task_id
                            ):
                                st.success("Chatverlauf gelöscht.")
                                st.rerun()
                            else:
                                st.error("Fehler beim Löschen des Chatverlaufs.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown(f"*{task[2]}*" if task[2] else "*Keine Beschreibung.*")

                    for msg in chat_history:
                        role = msg.get("role")
                        content = msg.get("content", "")
                        if role == "user":
                            st.chat_message("user").write(content)
                        elif role == "assistant":
                            st.chat_message("assistant").write(content)

                    user_input = st.chat_input("Nachricht eingeben...")
                    if user_input:
                        try:
                            chat_with_deepseek(
                                user_message=user_input,
                                user_id=st.session_state["user_id"],
                                event_id=st.session_state.selected_event_id,
                                task_id=st.session_state.selected_task_id
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Senden der Nachricht: {e}")
                else:
                    # Aufgabenliste anzeigen (für alle anderen Fälle)
                    st.subheader("🗂️ Aufgaben")

                    per_page = 4
                    total_pages = max(1, (len(tasks) + per_page - 1) // per_page)
                    page_number = st.number_input("Seite", min_value=1, max_value=total_pages, value=1, key=f"page_{event_id}")
                    start, end = (page_number - 1) * per_page, page_number * per_page
                    tasks_page = tasks[start:end]

                    for row in range(0, len(tasks_page), 2):
                        cols = st.columns(2)
                        for col_idx in range(2):
                            task_index = row + col_idx
                            if task_index < len(tasks_page):
                                task = tasks_page[task_index]
                                task_id, task_title, task_content = task[:3]
                                with cols[col_idx]:
                                    # Karte mit normalem Layout
                                    st.markdown(f"""
                                    <div class="task-card">
                                        <div class="task-card-content">
                                            <h4>{task_title}</h4>
                                            <p>{task_content or "Keine Beschreibung"}</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Normaler Streamlit-Button
                                    if st.button("Chat öffnen", key=f"open_chat_{task_id}_{event_id}_{idx}", 
                                               use_container_width=True):
                                        st.session_state.selected_task_id = task_id
                                        st.session_state.selected_event_id = event_id
                                        st.rerun()

    elif page == "Export":
        import pandas as pd
        import io, base64, requests
        from utils.event_manager import load_events, load_shared_events
        from utils.import_data import create_download_link

        display_page_header("Export")

        # CSS Styling passend zum NoteMaster-Export-Design
        st.markdown("""
        <style>
        .export-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .export-card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            border-left: 5px solid #4A90E2;
            height: 100%;
        }
        .import-card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            border-left: 5px solid #E24A90;
            height: 100%;
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

        
        # ℹ️ Hinweisbox oben
        st.markdown("""
        <div style="background-color: #eaf4fb; border-left: 5px solid #4A90E2; padding: 16px; border-radius: 6px; margin-bottom: 32px;">
            Diese Funktion erlaubt dir, deine Daten lokal zu speichern und später wiederherzustellen.
        </div>
        """, unsafe_allow_html=True)

        # Zwei-Spalten Layout
        col1, col2 = st.columns(2)

        # ------------------- EXPORT (Linke Spalte) ------------------- #
        with col1:
            st.markdown("### 📤 Events und Aufgaben exportieren")
            st.write("Wähle die Events aus, die du exportieren möchtest, und das gewünschte Format.")

            # Events laden
            personal_events = load_events(st.session_state["user_id"]) or []
            shared_events = load_shared_events(st.session_state["user_id"]) or []

            all_events = [(e[0], e[1], "Persönlich", e[2]) for e in personal_events]
            all_events += [(e[0], e[1], f"Geteilt von {e[2]}", e[3]) for e in shared_events]

            if all_events:
                event_options = [f"{e[1]} ({e[2]})" for e in all_events]
                selected_events = st.multiselect("Wähle Events zum Exportieren", event_options, default=event_options)

                selected_event_ids = [all_events[event_options.index(e)][0] for e in selected_events]

                export_format = st.radio("Exportformat auswählen", ["CSV", "Excel"], horizontal=True)
                include_stats = st.checkbox("Statistiken einbeziehen", value=True)
                include_tasks = st.checkbox("Aufgaben einbeziehen", value=True)

                if st.button("Export vorbereiten"):
                    if not selected_event_ids:
                        st.warning("Bitte wähle mindestens ein Event aus.")
                    else:
                        export_data = []

                        for event_id in selected_event_ids:
                            event = next((e for e in all_events if e[0] == event_id), None)
                            if not event:
                                continue

                            event_id, event_title, event_type, event_desc = event
                            tasks = load_tasks(event_id) if include_tasks else []
                            stats = load_stats(st.session_state["user_id"], event_id) if include_stats else []

                            event_data = {
                                "Event ID": event_id,
                                "Titel": event_title,
                                "Typ": event_type,
                                "Beschreibung": event_desc
                            }

                            if not tasks:
                                export_data.append(event_data)
                            else:
                                for task in tasks:
                                    task_id, task_title, task_content = task[0], task[1], task[2]
                                    task_data = event_data.copy()
                                    task_data.update({
                                        "Aufgabe ID": task_id,
                                        "Aufgabe Titel": task_title,
                                        "Aufgabe Inhalt": task_content
                                    })

                                    if include_stats:
                                        task_stats = [s for s in stats if s[2] == task_id]
                                        if task_stats:
                                            latest = task_stats[-1]
                                            task_data.update({
                                                "Letzte Bewertung": latest[1],
                                                "Datum": latest[3] if len(latest) > 3 else "Unbekannt"
                                            })

                                    export_data.append(task_data)

                        df = pd.DataFrame(export_data)
                        filename = "events_export"

                        if export_format == "CSV":
                            st.markdown(create_download_link(df, f"{filename}.csv", "📥 CSV-Datei herunterladen"), unsafe_allow_html=True)
                        else:
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                                df.to_excel(writer, sheet_name="Events", index=False)
                            b64 = base64.b64encode(output.getvalue()).decode()
                            st.markdown(
                                f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx" class="download-button">📥 Excel-Datei herunterladen</a>',
                                unsafe_allow_html=True
                            )
            else:
                st.info("Keine Events verfügbar.")

            st.markdown('</div>', unsafe_allow_html=True)  # END EXPORT-CARD

        # ------------------- IMPORT (Rechte Spalte) ------------------- #
        with col2:
            st.markdown("### 📥 Events und Aufgaben importieren")
            st.write("Importiere Events, Aufgaben und ggf. Bewertungen aus einer CSV- oder Excel-Datei.")

            uploaded_file = st.file_uploader("Datei auswählen (CSV oder Excel)", type=["csv", "xlsx"])

            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                        file_type = "csv"
                    else:
                        df = pd.read_excel(uploaded_file)
                        file_type = "xlsx"

                    st.success("✅ Datei erfolgreich geladen.")
                    show_mascot_reaction("success", "Datei erfolgreich geladen!")
                    st.dataframe(df.head(), use_container_width=True)

                    required_columns = {
                        "Event ID", "Titel", "Typ", "Beschreibung",
                        "Aufgabe ID", "Aufgabe Titel", "Aufgabe Inhalt"
                    }

                    if required_columns.issubset(df.columns):
                        if st.button("📤 Import starten"):
                            response = requests.post(
                                f"{API_URL}/import/events",
                                params={
                                    "user_id": st.session_state["user_id"],
                                    "file_type": file_type
                                },
                                files={"file": uploaded_file.getvalue()}
                            )
                            if response.status_code == 200:
                                st.success("🎉 Import abgeschlossen!")
                                show_mascot_reaction("success", "Import erfolgreich abgeschlossen!")
                                st.rerun()
                            else:
                                st.error(f"❌ Fehler: {response.json().get('error')}")
                    else:
                        st.error("❌ Datei muss folgende Spalten enthalten: " + ", ".join(required_columns))

                except Exception as e:
                    st.error(f"❌ Fehler beim Verarbeiten der Datei: {e}")

            st.markdown('</div>', unsafe_allow_html=True)  # END IMPORT-CARD


    elif page == "Tasks":
        display_page_header("Tasks")
        st.markdown("""
        <style>
        input[type="text"],
        textarea,
        .stTextInput > div > div > input,
        .stTextArea > div > textarea,
        .stNumberInput input {
            border-radius: 10px !important;
            border: 2px solid #4A90E2 !important;
            padding: 0.5rem !important;
        }

        .stButton > button {
            background-color: #4A90E2 !important;
            color: white !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.3rem !important;
            font-weight: 600;
            border: none !important;
            transition: 0.2s all ease-in-out;
        }

        .stButton > button:hover {
            background-color: #357ABD !important;
            transform: translateY(-2px);
        }

        /* Optional: Karten oder Container */
        .task-card, .quiz-card {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
            padding: 1rem;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
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
        display_page_header("Rätsel")
        st.markdown("""
        <style>
        input[type="text"],
        textarea,
        .stTextInput > div > div > input,
        .stTextArea > div > textarea,
        .stNumberInput input {
            border-radius: 10px !important;
            border: 2px solid #4A90E2 !important;
            padding: 0.5rem !important;
        }

        .stButton > button {
            background-color: #4A90E2 !important;
            color: white !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.3rem !important;
            font-weight: 600;
            border: none !important;
            transition: 0.2s all ease-in-out;
        }

        .stButton > button:hover {
            background-color: #357ABD !important;
            transform: translateY(-2px);
        }

        /* Optional für Kartenlayout */
        .quiz-card, .task-card {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
            padding: 1rem;
            margin-bottom: 1rem;
        }</style>
        """, unsafe_allow_html=True)

        events = load_events(st.session_state["user_id"])
        if events:
            selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="quiz_event_selection")
            selected_event_id = next(event[0] for event in events if event[1] == selected_event)
            quiz_mode(st.session_state["user_id"], selected_event_id)
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Statistiken":
        display_page_header("Lernfortschritt & Statistiken")
        events = load_events(st.session_state["user_id"])
        
        if events:
            # Auswahl zwischen Gesamtübersicht und spezifischem Event
            view_option = st.radio(
                "Ansicht wählen",
                ["Gesamtübersicht", "Spezifisches Event"],
                horizontal=True
            )
            
            if view_option == "Spezifisches Event":
                selected_event = st.selectbox(
                    "Event auswählen",
                    [event[1] for event in events],
                    key="stats_event_selection"
                )
                selected_event_id = next(event[0] for event in events if event[1] == selected_event)
                display_event_statistics(st.session_state["user_id"], selected_event_id)
            else:
                display_event_statistics(st.session_state["user_id"])
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Profil":
        # CSS für das Profil-Design
        st.markdown("""
        <style>
        
        .profile-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .profile-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #4A90E2;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        .profile-form .stTextInput {
            margin-bottom: 1rem !important;
        }
        .profile-form .stButton>button {
            width: 100% !important;
            margin-top: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            
            # Profilheader mit Avatar
            st.markdown('<div class="profile-header">', unsafe_allow_html=True)
            st.markdown(f'<div class="profile-avatar">{st.session_state["username"][0].upper()}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div>
                <h3 style="margin:0;">{st.session_state["username"]}</h3>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            profilstatus = "🌟 Premium-Nutzer" if st.session_state.get("is_premium") else "🔓 Kostenloses Konto"
            farbe = "green" if st.session_state.get("is_premium") else "gray"

            st.markdown(f"""
                <div style="padding:1rem; background-color:#f0f2f5; border-left:6px solid {farbe}; border-radius:10px; margin-bottom:1rem;">
                    <strong>Status:</strong> <span style="color:{farbe}; font-weight:bold;">{profilstatus}</span><br>
                    { "Du hast unbegrenzten Zugriff auf alle Funktionen." if st.session_state.get("is_premium") else "Du kannst bis zu 3 Events erstellen. Upgrade auf Premium für mehr!" }
                </div>
            """, unsafe_allow_html=True)

            if not st.session_state.get("is_premium"):
                if st.button("Jetzt auf Premium upgraden", key="upgrade_profile_button"):
                    conn = create_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET is_premium = 1 WHERE id = ?", (st.session_state.user_id,))
                        conn.commit()
                        conn.close()
                    st.session_state.is_premium = True
                    cookies = st.session_state.get("cookies")
                    cookies["is_premium"] = "1"
                    cookies.save()
                    st.success("Dein Konto wurde auf Premium umgestellt.")
                    st.rerun()
            
            # Bearbeitungsformular
            with st.form("profile_form"):
                st.markdown("### Kontoeinstellungen")
                
                new_username = st.text_input(
                    "Benutzername", 
                    value=st.session_state["username"],
                    help="Ändern Sie Ihren Anzeigenamen"
                )
                
                new_password = st.text_input(
                    "Neues Passwort", 
                    type="password",
                    placeholder="••••••••",
                    help="Mindestens 8 Zeichen"
                )
                
                confirm_password = st.text_input(
                    "Passwort bestätigen", 
                    type="password",
                    placeholder="••••••••"
                ) 
                
                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.form_submit_button(
                        "Änderungen speichern",
                        type="primary",
                        use_container_width=True
                    )
                with col2:
                    if st.form_submit_button(
                        "Abbrechen",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.rerun()
                
                if save_clicked:
                    if new_password and new_password != confirm_password:
                        st.error("Passwörter stimmen nicht überein!")
                    else:
                        success = update_profile(
                            st.session_state["user_id"],
                            new_username if new_username != st.session_state["username"] else None,
                            new_password if new_password else None
                        )
                        if success:
                            st.session_state["username"] = new_username
                            st.success("Profil aktualisiert!")
                            show_mascot_reaction("success", "profil erfolgreich aktualisiert!")
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)  # Ende profile-card
            
            # Logout-Button außerhalb der Karte
            if st.button("🚪 Ausloggen", key="logout_button"):
                logout()
                st.session_state["show_login"] = True
                st.session_state["show_register"] = False


    elif page == "Einstellungen":
        st.markdown("## ⚙️ Einstellungen")
        
        # Dunkelmodus-Toggle mit Symbolen
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write("")  # Platzhalter für Alignment
        with col2:
            dark_mode = st.toggle(
                "🌙 Dunkelmodus aktivieren",
                value=st.session_state.get("dark_mode", False),
                key="dark_mode_toggle"
            )
        
        # Zustand speichern und Cookies aktualisieren
        if dark_mode != st.session_state.get("dark_mode", False):
            st.session_state.dark_mode = dark_mode
            if "cookies" in st.session_state:
                st.session_state.cookies["dark_mode"] = "true" if dark_mode else "false"
                st.session_state.cookies.save()
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


# Sichtbarer, großer Footer mit Icons
st.markdown(""" 
<style> 
.footer {     
    position: fixed;
    bottom: 0;
    right: 0;
    width: calc(100% - 21rem); /* Sidebar-Breite abziehen */
    background-color: white;
    text-align: center;     
    color: #333;     
    font-size: 1rem;     
    font-weight: 500;     
    padding: 1rem 0;     
    z-index: 1000;
} 

.footer a {     
    color: #4A90E2;     
    text-decoration: none;     
    font-weight: bold;     
    margin: 0 1rem;     
    font-size: 1.05rem; 
} 

.footer a:hover {     
    text-decoration: underline; 
} 

.footer-icon {     
    margin-right: 6px; 
} 

/* Hauptinhalt Padding hinzufügen, damit er nicht vom Footer überdeckt wird */
.main .block-container {
    padding-bottom: 100px;
}

/* Responsive Anpassung für kleinere Bildschirme */
@media (max-width: 768px) {
    .footer {
        width: 100%;
        right: 0;
    }
}
</style>  

<div class="footer">     
    📢 Entwickelt mit ❤️ von deinem <strong>EventManager-Team</strong><br><br>     
    <a href="https://github.com" target="_blank">         
        <span class="footer-icon">📂</span>GitHub     
    </a>     
    <a href="https://youtube.com" target="_blank">         
        <span class="footer-icon">🎥</span>Readme     
    </a> 
</div> 
""", unsafe_allow_html=True)
