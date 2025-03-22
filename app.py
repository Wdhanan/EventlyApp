import logging
import streamlit as st
from dotenv import load_dotenv
from utils.auth import register, login, logout, load_all_users
from utils.event_manager import create_event, edit_event, delete_event, load_events, load_shared_events, load_tasks, share_event
from utils.task_manager import save_task, edit_task, delete_task, load_shared_tasks
from utils.event_question_generator import quiz_mode
from utils.event_stats_manager import load_stats, display_event_statistics
import os

# Umgebungsvariablen laden
load_dotenv()

# Farben für die Anwendung
PRIMARY_COLOR = "#4A90E2"  # Blau
SECONDARY_COLOR = "#F5F5F5"  # Hellgrau
TERTIARY_COLOR = "#333333"  # Dunkelgrau
ACCENT_COLOR = "#FFA500"  # Orange

# Custom CSS für einheitliches Design
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {SECONDARY_COLOR};
        color: {TERTIARY_COLOR};
    }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {ACCENT_COLOR};
    }}
    .stHeader {{
        color: {PRIMARY_COLOR};
    }}
    .stSidebar {{
        background-color: {PRIMARY_COLOR};
        color: white;
    }}
    .stExpander {{
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    .divider {{
        border-top: 2px solid {PRIMARY_COLOR};
        margin: 1rem 0;
    }}
    .note-grid {{
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 1rem;
    }}
    .note-list {{
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    .note-form {{
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Titel der Anwendung
st.title("📅 EventManager")
st.write("Willkommen beim EventManager! Eine Anwendung, um deine Events zu planen und zu verwalten.")

# Zustandsvariablen initialisieren
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "api_key_configured" not in st.session_state:
    st.session_state["api_key_configured"] = os.getenv("DEEPSEEK_API_KEY") is not None
if "deepseek_api_key" not in st.session_state:
    st.session_state["deepseek_api_key"] = os.getenv("DEEPSEEK_API_KEY", "")
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False  # Standardmäßig ist der Dunkelmodus deaktiviert

# Dunkelmodus anwenden (nur auf den Hauptinhalt)
if st.session_state["dark_mode"]:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Seitenleiste für Navigation
st.sidebar.title("Navigation")
if not st.session_state["api_key_configured"]:
    page = st.sidebar.radio(
        "Wähle eine Seite",
        ["API-Key konfigurieren"],
        key="auth_navigation"
    )
else:
    if not st.session_state["logged_in"]:
        page = st.sidebar.radio(
            "Wähle eine Seite",
            ["Login", "Registrierung", "API-Key bearbeiten"],
            key="auth_navigation"
        )
    else:
        page = st.sidebar.radio(
            "Wähle eine Seite",
            ["Dashboard", "Events", "Tasks", "Rätsel", "Statistiken", "Profil", "Einstellungen", "Über die Anwendung"],
            key="main_navigation"
        )

# Hauptinhalt basierend auf der ausgewählten Seite
if page == "API-Key konfigurieren" or page == "API-Key bearbeiten":
    st.header("API-Key konfigurieren")
    with st.container():
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
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
    if page == "Login":
        login()
    elif page == "Registrierung":
        register()
else:
    if page == "Dashboard":
        st.header("Dashboard")
        st.write("Hier siehst du eine Übersicht deiner Aktivitäten.")
        events = load_events(st.session_state["user_id"])
        stats = load_stats(st.session_state["user_id"])

        # Anzahl der Events
        num_events = len(events) if events else 0
        st.write(f"**Anzahl der Events:** {num_events}")

        # Anzahl der Quizze
        num_quizzes = len(stats) if stats else 0
        st.write(f"**Anzahl der durchgeführten Rätsel:** {num_quizzes}")

        # Durchschnittliche Punktzahl
        if stats:
            total_score = sum(stat[1] for stat in stats)
            average_score = total_score / num_quizzes
            st.write(f"**Durchschnittliche Punktzahl:** {average_score:.2f}/25")
        else:
            st.write("**Durchschnittliche Punktzahl:** Noch keine Rätsel durchgeführt.")

    elif page == "Events":
        st.header("📅 Events")
        with st.container():
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.write("### Erstelle oder bearbeite Events")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("#### Erstellte Events")
                events = load_events(st.session_state["user_id"])
                if events:
                    selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="event_selection")
                    selected_event_id = next(event[0] for event in events if event[1] == selected_event)
                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        if st.button("✏️ Bearbeiten", key="edit_event_button"):
                            st.session_state["edit_event_id"] = selected_event_id
                    with col1_2:
                        if st.button("🗑️ Löschen", key="delete_event_button"):
                            delete_event(selected_event_id)
                            st.rerun()
                shared_events = load_shared_events(st.session_state["user_id"])
                logging.info("Geladene geteilte Events: %s", shared_events)
                if shared_events:
                    st.write("### Geteilte Events")
                    for event in shared_events:
                        st.write(f"**Event:** {event[1]} (Geteilt von {event[2]})")
                else:
                    st.warning("Keine geteilten Events gefunden.")

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
                            del st.session_state["edit_event_id"]
                        else:
                            create_event(st.session_state["user_id"], title, description)
                        st.rerun()
                with col2_2:
                    if st.button("Abbrechen", key="cancel_event_button"):
                        if "edit_event_id" in st.session_state:
                            del st.session_state["edit_event_id"]
                        st.rerun()

                st.write("#### Event teilen")
                all_users = load_all_users()
                if all_users and events:  # Überprüfe, ob Events vorhanden sind
                    shared_with_username = st.selectbox(
                        f"Event mit Benutzer teilen",
                        [user for user in all_users if user != st.session_state["username"]],  # Zeige nur andere Benutzer an
                        key=f"share_event_{selected_event_id}"
                    )
                    if st.button(f"Event {selected_event} teilen", key=f"share_button_{selected_event_id}"):
                        share_event(selected_event_id, st.session_state["user_id"], shared_with_username)
                else:
                    st.warning("Keine anderen Benutzer oder Events gefunden.")

    elif page == "Tasks":
        st.header("📝 Tasks")
        with st.container():
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
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
                else:
                    st.warning("Keine Tasks gefunden.")

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
            else:
                st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Rätsel":
        events = load_events(st.session_state["user_id"])
        if events:
            selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="quiz_event_selection")
            selected_event_id = next(event[0] for event in events if event[1] == selected_event)
            quiz_mode(st.session_state["user_id"], selected_event_id)
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Statistiken":
        st.header("Statistiken")
        events = load_events(st.session_state["user_id"])
        if events:
            selected_event = st.selectbox("Wähle ein Event", [event[1] for event in events], key="stats_event_selection")
            selected_event_id = next(event[0] for event in events if event[1] == selected_event)
            display_event_statistics(st.session_state["user_id"], selected_event_id)
        else:
            st.warning("Keine Events gefunden. Bitte erstelle zuerst ein Event.")

    elif page == "Profil":
        st.header("Profil")
        st.write(f"Eingeloggt als: {st.session_state['username']}")
        if st.button("Ausloggen", key="logout_button"):
            logout()

    elif page == "Einstellungen":
        st.header("Einstellungen")
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
        st.header("Über die Anwendung")
        st.write("""
            ## EventManager – Dein Assistent für die Eventplanung
            Der EventManager ist eine Webanwendung, die dir hilft, Events effektiv zu planen und zu verwalten. 
            Mit dieser Anwendung kannst du:
            - **Events erstellen und verwalten**
            - **Aufgaben (Tasks) für Events hinzufügen**
            - **Fragen basierend auf den Aufgaben generieren**
            - **Deine Fortschritte verfolgen**

            ### Wie funktioniert es?
            1. **Events erstellen**: Gib deine Events ein (z. B. "Hochzeit", "Geburtstagsfeier").
            2. **Aufgaben hinzufügen**: Füge Aufgaben für jedes Event hinzu (z. B. "Location buchen", "Catering bestellen").
            3. **Rätsel-Modus**: Beantworte Fragen basierend auf den Aufgaben und überprüfe dein Wissen.
            4. **Statistiken**: Verfolge deine Fortschritte und verbessere dich.

            ### DeepSeek API-Key
            Um Fragen zu generieren, benötigst du einen DeepSeek API-Key. 
            Du kannst diesen kostenlos auf [OpenRouter](https://openrouter.ai) erstellen.
        """)