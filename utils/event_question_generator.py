from datetime import datetime
import os
import json
import logging
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from utils.auth import get_user_premium_status_and_quiz_limits, update_user_quiz_count
from utils.mascot_reactions import show_mascot_reaction
from utils.chat_api import save_chat_message_direct
from utils.database import create_connection, get_event_by_id, get_task_by_id, get_tasks_by_event_id
from utils.task_manager import load_tasks, load_shared_tasks
from utils.event_stats_manager import save_stats
from sqlite3 import Error

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Configuration API
def get_openai_client():
    """Initialisiert den OpenAI-Client mit Fehlerbehandlung"""
    try:
        # 1. Prüfe Streamlit Secrets
        api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
        
        # 2. Fallback zu manueller Eingabe im Session State
        if not api_key and "deepseek_api_key" in st.session_state:
            api_key = st.session_state.deepseek_api_key
            
        if not api_key:
            st.error("API-Key nicht gefunden. Bitte konfigurieren Sie den Key zuerst.")
            return None
            
        return OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        )
    except Exception as e:
        st.error(f"Fehler bei Client-Initialisierung: {str(e)}")
        return None

client = get_openai_client()

# Verzeichnis für Fragen
QUESTIONS_DIR = "data/questions"
os.makedirs(QUESTIONS_DIR, exist_ok=True)
API_URL = "http://localhost:8000"
DAILY_QUIZ_LIMIT_FREE = 5


def generate_questions(event_title, tasks):
    """
    Generiert Fragen basierend auf den Tasks eines Events mithilfe der DeepSeek-API.
    :param event_title: Titel des Events
    :param tasks: Liste der Tasks des Events (jeder Task ist ein Tupel: (id, title, content))
    :return: Eine Liste von generierten Fragen
    """
    try:
        # Kombiniere den Inhalt aller Tasks zu einem einzigen Text
        combined_content = "\n".join([f"{task[1]}: {task[2]}" for task in tasks])  # task[1] = title, task[2] = content

        prompt = (
        f"Generiere 5 präzise Fragen basierend auf den folgenden Aufgaben eines Events. Die Fragen sollten:\n"
        f"- Konkrete Fortschritte und Entscheidungen im Arbeitsprozess erfragen\n"
        f"- Auf die tatsächlich durchgeführten Schritte eingehen (nicht nur allgemeine Fragen)\n"
        f"- Messbare Kriterien für den Bearbeitungsstand abfragen\n"
        f"- In JSON-Format zurückgegeben werden: [{{\"frage\": \"Frage\", \"antwort\": \"Musterantwort\"}}]\n\n"
        f"Beispiel für gute Fragen:\n"
        f"- \"Bei wie vielen Locations haben Sie angefragt und wie viele haben geantwortet?\"\n"
        f"- \"Welche konkreten Vergleichskriterien waren für die Auswahl entscheidend?\"\n"
        f"- \"Welche Meilensteine wurden bereits erreicht und welche stehen noch aus?\"\n\n"
        f"Aufgaben: {combined_content}\n"
        f"Gib nur das JSON zurück, nichts anderes."
    )

        # Sende die Anfrage an die API
        response = client.chat.completions.create(
            extra_body={},
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        # Überprüfe die Antwort
        logging.info("API-Antwort: %s", response)
        generated_text = response.choices[0].message.content.strip()
        if generated_text.startswith("```json") and generated_text.endswith("```"):
            generated_text = generated_text.strip("```json").strip("```")
        if not generated_text:
            st.error("Leere Antwort von der API erhalten.")
            return []

        # Lade das JSON
        try:
            questions = json.loads(generated_text)
        except json.JSONDecodeError as json_err:
            logging.error("Fehler beim Parsen des JSON: %s", json_err)
            st.error("Die API-Antwort ist kein gültiges JSON.")
            return []

        # Speichere die Fragen in einer JSON-Datei
        json_file_path = os.path.join(QUESTIONS_DIR, f"{event_title}.json")
        with open(json_file_path, "w") as file:
            json.dump(questions, file, indent=4, ensure_ascii=False)
        logging.info("Fragen gespeichert in: %s", json_file_path)
        return questions

    except Exception as e:
        logging.error("Fehler bei der Generierung der Fragen: %s", e)
        st.error(f"Fehler bei der Generierung der Fragen: {e}")
        return []

def load_questions(event_title):
    """
    Lädt die gespeicherten Fragen für ein bestimmtes Event.
    :param event_title: Titel des Event
    :return: Liste der Fragen
    """
    json_file_path = os.path.join(QUESTIONS_DIR, f"{event_title}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as file:
            return json.load(file)
    return []


def quiz_mode(user_id, event_id, task_id, questions):
    """
    Führt den Quiz-Modus für die generierten Fragen aus.
    """
    is_premium, daily_quiz_count, last_quiz_reset = get_user_premium_status_and_quiz_limits(user_id)
    today = datetime.now().date()

    # Reset des Zählers, falls der Tag gewechselt hat
    if last_quiz_reset:
        try:
            last_reset_date = datetime.fromisoformat(last_quiz_reset).date()
            if last_reset_date < today:
                update_user_quiz_count(user_id) # Setzt den Zähler auf 1 und aktualisiert das Reset-Datum
                daily_quiz_count = 1 # Nach dem Reset ist der Zähler 1
        except ValueError:
            # Falls das Datum ungültig ist, behandeln wir es als nicht gesetzt
            update_user_quiz_count(user_id)
            daily_quiz_count = 1
    elif not last_quiz_reset:
        # Wenn last_quiz_reset noch nie gesetzt wurde
        update_user_quiz_count(user_id)
        daily_quiz_count = 1

    # Überprüfung des Limits für kostenlose Nutzer
    if not is_premium and daily_quiz_count > DAILY_QUIZ_LIMIT_FREE:
        st.warning(f"Du hast dein tägliches Limit von {DAILY_QUIZ_LIMIT_FREE} Quizfragen erreicht.")
        st.info("💡 Upgrade auf Premium, um unbegrenzt Quizfragen zu erhalten!")
        # Hier können wir einen Button zum Upgrade anzeigen, wie in event_manager.py
        if st.button("Jetzt upgraden für unbegrenzte Quizfragen"):
            conn = create_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET is_premium = 1 WHERE id = ?", (user_id,))
                    conn.commit()
                    st.success("Profil erfolgreich auf Premium umgestellt! Du kannst jetzt unbegrenzt Quizfragen stellen.")
                    st.session_state.is_premium = True
                    # Optional: Aktualisiere Cookies, falls Streamlit sie verwendet
                    cookies = st.session_state.get("cookies")
                    if cookies:
                        cookies["is_premium"] = "1"
                        cookies.save()
                    st.rerun() # Rerun, um den neuen Premium-Status sofort anzuwenden
                except Error as e:
                    st.error(f"Fehler beim Premium-Upgrade: {e}")
                finally:
                    conn.close()
        return # Beende die Funktion, wenn das Limit erreicht ist

    # Wenn wir hier sind, ist der Benutzer Premium oder hat noch Versuche übrig.
    # Aktualisiere den Zähler für diesen Quiz-Versuch (nur für nicht-Premium-Benutzer, da Premium unbegrenzt ist)
    if not is_premium:
        updated_count, success = update_user_quiz_count(user_id)
        if not success:
            st.error("Es gab ein Problem beim Aktualisieren deines Quiz-Zählers. Bitte versuche es später erneut.")
            return

    # Der Rest der bestehenden `quiz_mode`-Funktion, die die Quizfragen anzeigt
    # ... (bestehender Quiz-Modus-Code) ...
    # Bevor die Fragen generiert werden, stellen wir sicher, dass das Limit nicht überschritten wurde.
    # Dies ist bereits oben in `quiz_mode` integriert.

    if not questions:
        st.warning("Keine Fragen zum Quiz gefunden. Bitte generiere zuerst Fragen.")
        return

    st.subheader(f"Quiz für Event: {get_event_by_id(event_id)[2]}")

    current_question_index = st.session_state.get('current_question_index', 0)
    user_scores = st.session_state.get('user_scores', {})
    
    if current_question_index < len(questions):
        question_data = questions[current_question_index]
        question_text = question_data['question']
        correct_answer = question_data['answer']
        options = question_data.get('options', [])

        st.markdown(f"**Frage {current_question_index + 1}/{len(questions)}:**")
        st.write(question_text)

        user_answer = st.text_input("Deine Antwort:", key=f"answer_{current_question_index}")

        if st.button("prüfen", key=f"submit_{current_question_index}"):
            if user_answer.strip().lower() == correct_answer.strip().lower():
                score = 100
                st.success("Richtig!")
                show_mascot_reaction("success", "Super! Das war richtig!")
            else:
                score = 0
                st.error(f"Falsch. Die richtige Antwort war: **{correct_answer}**")
                show_mascot_reaction("error", "Leider falsch. Versuch es noch einmal!")
            
            user_scores[current_question_index] = score
            save_user_feedback(question_text, user_answer, score) # Speichern des Feedbacks
            
            # Speichern der Statistik für diese Aufgabe/Frage
            save_stats(user_id, event_id, task_id, score)
            st.session_state.user_scores = user_scores

            st.session_state.current_question_index += 1
            st.rerun()
    else:
        st.success("Quiz beendet!")
        total_score = sum(user_scores.values())
        avg_score = total_score / len(questions) if questions else 0
        st.write(f"Dein durchschnittlicher Score: {avg_score:.2f}%")
        show_mascot_reaction("info", f"Quiz beendet! Dein Score: {avg_score:.2f}%")

        if st.button("Quiz erneut starten"):
            st.session_state.current_question_index = 0
            st.session_state.user_scores = {}
            st.rerun()


def evaluate_answer(question, user_answer, correct_answer):
    """
    Bewertet die Antwort des Benutzers mithilfe der DeepSeek-API.
    :param question: Die gestellte Frage
    :param user_answer: Die Antwort des Benutzers
    :param correct_answer: Die korrekte Antwort
    :return: Ein Dictionary mit der Bewertung
    """
    try:
        prompt = (
            f"Bewerte die Antwort als Lehrer (1-5 Punkte) mit Fokus auf:\n"
            f"1. Erwähnung konkreter Schritte/Meilensteine\n"
            f"2. Nennung von Zahlen/Daten/Fristen\n"
            f"3. Entscheidungskriterien\n"
            f"4. Aktueller Stand des Prozesses\n\n"
            f"Frage: {question}\n"
            f"Idealantwort: {correct_answer}\n"
            f"Schülerantwort: {user_answer}\n\n"
            f"Bewertungsregeln:\n"
            f"- 5 Punkte: Enthält alle relevanten Prozessschritte + quantitative Angaben\n"
            f"- 4 Punkte: Nennt Hauptschritte aber wenig Details\n"
            f"- 3 Punkte: Allgemeine Aussagen ohne konkreten Bezug\n"
            f"- 2 Punkte: Nur teilweise relevant\n"
            f"- 1 Punkt: Kein Bezug zur Frage\n\n"
            f"Gib NUR JSON zurück: {{\"score\": X, \"feedback\": \"kurzes konstruktives Feedback\"}}"
        )

        response = client.chat.completions.create(
            extra_body={},
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
        )

        if not response or not response.choices:
            raise ValueError("Die API hat keine gültige Antwort zurückgegeben.")

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError("Die API-Antwort ist leer.")

        # Bereinige das JSON
        cleaned_content = raw_content.strip().strip("```json").strip("```")
        cleaned_content = cleaned_content.replace("'", '"')

        try:
            evaluation = json.loads(cleaned_content)
        except json.JSONDecodeError:
            # Versuche, die Punktzahl direkt zu extrahieren
            score_match = re.search(r'score["\']?\s*:\s*(\d+)', cleaned_content)
            if score_match:
                return {"score": int(score_match.group(1))}
            raise

        if "score" not in evaluation:
            raise ValueError("Das JSON enthält nicht den Schlüssel 'score'.")
        

        save_user_feedback(question, user_answer, evaluation["score"])

        return {"score": evaluation["score"]}

    except Exception as e:
        logging.exception("Fehler bei der Bewertung der Antwort: %s", e)
        return {"score": 0}

def quiz_mode(user_id, event_id):
    from utils.database import get_event_by_id
    st.header("\U0001F9E9 Rätsel-Modus")

    event = get_event_by_id(event_id)
    if event:
        st.subheader(f"\U0001F4C5 Event: {event[1]}")
        with st.expander("ℹ️ Event-Beschreibung"):
            st.write(event[2] or "Keine Beschreibung.")

    tasks = load_tasks(event_id)
    shared_tasks = load_shared_tasks(user_id)
    all_tasks = tasks + shared_tasks

    if not all_tasks:
        st.warning("Keine Aufgaben vorhanden.")
        return

    task_titles = [task[1] for task in all_tasks]
    selected_task_title = st.selectbox("Wähle eine Aufgabe", task_titles, key="quiz_task_select")

    selected_task = next(task for task in all_tasks if task[1] == selected_task_title)

    with st.expander("\U0001F4CB Aufgabendetails"):
        st.write(selected_task[2] or "Keine Beschreibung.")

    # Initialisieren
    if "questions" not in st.session_state or st.session_state.get("current_task") != selected_task_title:
        st.session_state["questions"] = load_questions(selected_task_title)
        st.session_state["answers"] = {}
        st.session_state["skipped"] = set()
        st.session_state["current_index"] = 0
        st.session_state["quiz_finished"] = False
        st.session_state["current_task"] = selected_task_title

    # Fragen generieren
    if st.button("\U0001F504 Neue Fragen generieren"):
        questions = generate_questions(selected_task_title, [selected_task])
        if questions:
            st.session_state["questions"] = questions
            st.session_state["answers"] = {}
            st.session_state["skipped"] = set()
            st.session_state["current_index"] = 0
            st.session_state["quiz_finished"] = False
            st.success("Fragen wurden neu generiert.")

    questions = st.session_state["questions"]
    idx = st.session_state["current_index"]

    if questions and idx < len(questions) and not st.session_state["quiz_finished"]:
        q = questions[idx]
        st.write(f"### Frage {idx + 1} von {len(questions)}")
        st.markdown(f"**{q['frage']}**")

        key = f"answer_{idx}"
        skip_key = f"skip_{idx}"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.session_state["answers"][key] = st.text_area("Deine Antwort", key=key)
        with col2:
            if st.checkbox("Überspringen", key=skip_key):
                st.session_state["skipped"].add(idx)
            elif idx in st.session_state["skipped"]:
                st.session_state["skipped"].remove(idx)

        # Navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if idx > 0:
                if st.button("⬅️ Zurück"):
                    st.session_state["current_index"] -= 1
                    st.rerun()

        with nav_col3:
            if idx < len(questions) - 1:
                if st.button("➡️ Weiter"):
                    st.session_state["current_index"] += 1
                    st.rerun()
            else:
                if st.button("📝 prüfen"):
                    st.session_state["quiz_finished"] = True

    # Ergebnisanzeige
    if st.session_state["quiz_finished"]:
        st.markdown("---")
        st.subheader("📊 Ergebnis")

        total_score = 0
        answered = 0
        for i, q in enumerate(questions):
            if i in st.session_state["skipped"]:
                continue
            key = f"answer_{i}"
            answer = st.session_state["answers"].get(key, "")
            result = evaluate_answer(q["frage"], answer, q["antwort"])
            score = result["score"]
            save_stats(user_id, event_id, selected_task[0], score)
            total_score += score
            answered += 1

        if answered > 0:
            avg = total_score / answered
            if avg >= 4.5:
                badge = "\U0001F31F Hervorragend"
                color = "green"
            elif avg >= 3.5:
                badge = "\U0001F44D Gut"
                color = "blue"
            elif avg >= 2.5:
                badge = "\U0001F7E1 Mittel"
                color = "orange"
            else:
                badge = "\U0001F534 Schwach"
                color = "red"

            st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: #f9f9f9; border-radius: 10px;">
                    <h2 style="color: {color}; font-size: 2.5em;">{avg:.1f}/5</h2>
                    <p style="font-size: 1.2em;">{badge}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Alle Fragen wurden übersprungen.")

        # Navigation Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("\U0001F504 Nochmal versuchen"):
                st.session_state["quiz_finished"] = False
                st.session_state["current_index"] = 0
                st.session_state["answers"] = {}
                st.session_state["skipped"] = set()
                st.rerun()
        with col2:
            if st.button("📋 Andere Aufgabe wählen"):
                del st.session_state["questions"]
                del st.session_state["current_task"]
                st.session_state["quiz_finished"] = False
                st.rerun()


def chat_with_deepseek(user_message, event_id=None, task_id=None, user_id=None):
    """
    Optimierte Chatfunktion mit verbesserter Fehlerbehandlung
    """
    if not user_message or not user_message.strip():
        return "Bitte stellen Sie eine konkrete Frage."

    try:
        # 1. Nachricht senden
        msg_data = {
            "user_id": user_id,
            "event_id": event_id,
            "task_id": task_id,
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f"{API_URL}/chat/send",
                json=msg_data,
                timeout=10  # Timeout nach 10 Sekunden
            )
            response.raise_for_status()  # Wirft Exception für 4XX/5XX
        except requests.exceptions.RequestException as e:
            logging.error(f"API send error: {str(e)}")
            # Fallback: Direkt in DB speichern
            save_chat_message_direct(
                user_id, event_id, task_id, 
                "user", user_message, 
                datetime.now().isoformat()
            )

        # 2. KI-Antwort generieren
        prompt = build_prompt(user_message, event_id, task_id)
        ai_response = generate_ai_response(prompt)
        
        # 3. KI-Antwort speichern
        try:
            response = requests.post(
                f"{API_URL}/chat/send",
                json={
                    "user_id": user_id,
                    "event_id": event_id,
                    "task_id": task_id,
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"API send error: {str(e)}")
            # Fallback: Direkt in DB speichern
            save_chat_message_direct(
                user_id, event_id, task_id, 
                "assistant", ai_response, 
                datetime.now().isoformat()
            )

        return ai_response
        
    except Exception as e:
        logging.error(f"Error in chat_with_deepseek: {str(e)}")
        return f"Bezogen auf Ihre Aufgabe: Bitte überprüfen Sie den aktuellen Status und identifizieren Sie die nächsten Schritte."


def build_detailed_context(event_id=None, task_id=None, user_id=None):
    """
    Erstellt detaillierten Kontext für spezifische Antworten.
    
    Returns:
        dict: Kontextinformationen mit Event-, Task- und verwandten Daten
    """
    context = {
        'event': None,
        'task': None,
        'related_tasks': [],
        'event_progress': None,
        'user_stats': None
    }
    
    try:
        # Event-Kontext laden
        if event_id:
            event = get_event_by_id(event_id)
            if event:
                context['event'] = {
                    'id': event[0],
                    'title': event[2],
                    'description': event[3] if len(event) > 3 else None,
                    'created_at': event[5] if len(event) > 5 else None
                }
                
<<<<<<< HEAD
                # Alle Tasks des Events für besseren Kontext
                all_event_tasks = get_tasks_by_event_id(event_id)
                context['related_tasks'] = [
                    {
                        'id': task[0],
                        'title': task[2],
                        'content': task[3] if len(task) > 3 else None,
                        'status': task[4] if len(task) > 4 else 'in Bearbeitung'
                    }
                    for task in all_event_tasks
                ]
        
        # Spezifische Task-Kontext laden
        if task_id:
            task = get_task_by_id(task_id)
            if task:
                context['task'] = {
                    'id': task[0],
                    'event_id': task[1],
                    'title': task[2],
                    'content': task[3] if len(task) > 3 else None,
                    'status': task[4] if len(task) > 4 else 'in Bearbeitung'
                }
        
        # Benutzer-Statistiken für personalisierte Antworten
        if user_id and event_id:
            context['user_stats'] = get_user_event_stats(user_id, event_id)
            
    except Exception as e:
        logging.error(f"Fehler beim Aufbau des Kontexts: {str(e)}")
    
    return context


def get_recent_chat_history(user_id, event_id=None, task_id=None, limit=5):
    """
    Lädt die letzten Chat-Nachrichten für besseren Kontext.
    
    Returns:
        list: Liste der letzten Chat-Nachrichten
    """
    try:
        response = requests.get(f"{API_URL}/chat/history", params={
            "user_id": user_id,
            "event_id": event_id,
            "task_id": task_id
        })
        
        if response.status_code == 200:
            history = response.json()
            # Nur die letzten N Nachrichten zurückgeben
            return history[-limit*2:] if history else []
        
    except Exception as e:
        logging.error(f"Fehler beim Laden der Chat-Historie: {str(e)}")
    
    return []


def create_specialized_prompt(user_message, context_info, chat_history):
    """
    Erstellt einen spezialisierten Prompt basierend auf Kontext und Historie.
    
    Returns:
        str: Optimierter Prompt für die KI
    """
    prompt_parts = []
    
    # Basis-Rolle definieren
    prompt_parts.append(
        "Du bist ein spezialisierter Assistent für Event- und Aufgabenmanagement. "
        "Deine Aufgabe ist es, präzise, hilfreiche Antworten zu geben, die sich direkt "
        "auf die vorliegenden Events und Aufgaben beziehen."
    )
    
    # Event-Kontext hinzufügen
    if context_info['event']:
        event = context_info['event']
        prompt_parts.append(f"\n**AKTUELLES EVENT:**")
        prompt_parts.append(f"Titel: {event['title']}")
        if event['description']:
            prompt_parts.append(f"Beschreibung: {event['description']}")
    
    # Task-Kontext hinzufügen
    if context_info['task']:
        task = context_info['task']
        prompt_parts.append(f"\n**AKTUELLE AUFGABE:**")
        prompt_parts.append(f"Titel: {task['title']}")
        if task['content']:
            prompt_parts.append(f"Details: {task['content']}")
        prompt_parts.append(f"Status: {task['status']}")
    
    # Verwandte Aufgaben für Kontext
    if context_info['related_tasks']:
        prompt_parts.append(f"\n**VERWANDTE AUFGABEN IM EVENT:**")
        for i, related_task in enumerate(context_info['related_tasks'][:3], 1):
            prompt_parts.append(f"{i}. {related_task['title']} (Status: {related_task['status']})")
            if related_task['content'] and len(related_task['content']) < 100:
                prompt_parts.append(f"   → {related_task['content'][:100]}")
    
    # Chat-Historie für Kontinuität
    if chat_history:
        prompt_parts.append(f"\n**BISHERIGER GESPRÄCHSVERLAUF:**")
        for msg in chat_history[-4:]:  # Nur die letzten 4 Nachrichten
            role = "Nutzer" if msg['role'] == 'user' else "Assistent"
            content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
            prompt_parts.append(f"{role}: {content}")
    
    # Anweisungen für spezifische Antworten
    prompt_parts.append(f"\n**ANWEISUNGEN:**")
    prompt_parts.append("1. Beziehe dich IMMER auf die konkreten Aufgaben und Events")
    prompt_parts.append("2. Gib praktische, umsetzbare Ratschläge")
    prompt_parts.append("3. Erwähne spezifische Aufgabentitel wenn relevant")
    prompt_parts.append("4. Berücksichtige den aktuellen Status der Aufgaben")
    prompt_parts.append("5. Halte Antworten präzise und hilfreich (max. 200 Wörter)")
    
    # Benutzer-Frage
    prompt_parts.append(f"\n**NUTZERFRAGE:** {user_message}")
    
    prompt_parts.append(f"\n**ANTWORT:**")
    
    return "\n".join(prompt_parts)


def generate_ai_response(prompt):
    """
    Generiert KI-Antwort mit optimierten Parametern.
    
    Returns:
        str: KI-generierte Antwort
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Niedrigere Temperatur für fokussiertere Antworten
            max_tokens=500,   # Begrenzte Token-Anzahl für präzise Antworten
        )
        
        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Entschuldigung, ich konnte keine Antwort generieren."
            
    except Exception as e:
        logging.error(f"Fehler bei der KI-Antwort-Generierung: {str(e)}")
        return f"Es gab einen technischen Fehler. Bitte versuchen Sie es erneut."


def post_process_response(ai_response, context_info):
    """
    Nachbearbeitung der KI-Antwort für bessere Relevanz.
    
    Returns:
        str: Verbesserte Antwort
    """
    if not ai_response:
        return "Entschuldigung, ich konnte keine passende Antwort finden."
    
    # Füge Kontext-spezifische Hinweise hinzu
    enhanced_response = ai_response
    
    # Wenn spezifische Aufgabe: Hinweis auf andere verwandte Aufgaben
    if context_info['task'] and context_info['related_tasks']:
        task_title = context_info['task']['title']
        if task_title.lower() not in ai_response.lower():
            enhanced_response = f"**Bezogen auf '{task_title}':** " + enhanced_response
    
    # Kürze zu lange Antworten
    if len(enhanced_response) > 800:
        enhanced_response = enhanced_response[:750] + "...\n\n💡 *Für detailliertere Informationen stellen Sie gerne eine spezifischere Frage.*"
    
    return enhanced_response


def get_user_event_stats(user_id, event_id):
    """
    Lädt Benutzer-Statistiken für personalisierte Antworten.
    
    Returns:
        dict: Statistiken des Benutzers
    """
    try:
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_interactions,
                       AVG(score) as avg_score,
                       MAX(timestamp) as last_activity
                FROM stats 
                WHERE user_id = ? AND event_id = ?
            """, (user_id, event_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'total_interactions': result[0],
                    'avg_score': result[1],
                    'last_activity': result[2]
                }
    except Exception as e:
        logging.error(f"Fehler beim Laden der Benutzer-Statistiken: {str(e)}")
    
    return None


def save_user_feedback(question, user_answer, score):
    """Speichert Nutzerantworten zur Verbesserung der KI"""
    feedback_dir = "data/feedback"
    os.makedirs(feedback_dir, exist_ok=True)
    
    feedback = {
        "question": question,
        "user_answer": user_answer,
        "score": score,
        "timestamp": datetime.now().isoformat()
    }
    
    file_path = os.path.join(feedback_dir, f"feedback_{hash(question)}.json")
    with open(file_path, "w") as f:
        json.dump(feedback, f)


def build_prompt(user_message, event_id=None, task_id=None):
    context = ""
    if event_id:
        event = get_event_by_id(event_id)
        if event:
            context += f"Event: {event[2]}\nBeschreibung: {event[3]}\n"
    if task_id:
        task = get_task_by_id(task_id)
        if task:
            context += f"Aufgabe: {task[2]}\nDetails: {task[3]}\n"
    prompt = (
        f"Der Nutzer stellt eine Frage zu einem Event oder einer Aufgabe.\n"
        f"{context}"
        f"Frage: {user_message}\n"
        f"Bitte gib eine hilfreiche, prägnante Antwort, die auf das Event/den Task eingeht."
    )
    return prompt
=======
                # Wenn der Benutzer eine Antwort eingibt, speichere sie im session_state
                if user_answer:
                    st.session_state[answer_key] = user_answer  # Speichere die Antwort
                else:
                    all_answered = False  # Nicht alle Fragen wurden beantwortet

            # "Quiz abschließen"-Button anzeigen, wenn alle Fragen beantwortet wurden
            if all_answered:
                if st.button("Quiz abschließen", key="finish_quiz_button"):
                    total_score = 0  # Gesamtpunktzahl für diese Quiz-Session
                    max_score = len(questions) * 5  # Maximale Punktzahl basierend auf der Anzahl der Fragen

                    for i, question in enumerate(questions, start=1):
                        answer_key = f"user_answer_{i}"
                        user_answer = st.session_state[answer_key]
                        evaluation = evaluate_answer(question['frage'], user_answer, question['antwort'])
                        st.write(f"**Frage {i}:** {question['frage']}")
                        st.write(f"Deine Antwort: {user_answer}")
                        st.write(f"Bewertung: {evaluation['score']}/5")
                        total_score += evaluation["score"]  # Addiere die Punktzahl zur Gesamtpunktzahl

                    st.write(f"**Gesamtpunktzahl:** {total_score}/{max_score}")

                    selected_task_full = next(task for task in all_tasks if task[1] == selected_task)
                    task_id = selected_task_full[0]
                    # Speichere die Statistik, wenn alle Fragen beantwortet wurden
                    save_stats(user_id, event_id, task_id, total_score)
                    st.success("Quiz abgeschlossen! Deine Statistik wurde gespeichert.")
                    st.session_state["quiz_finished"] = True  # Markiere das Quiz als abgeschlossen

                    # Leere die Antwortfelder nach dem Abschluss des Quiz
                    for i in range(1, len(questions) + 1):
                        answer_key = f"user_answer_{i}"
                        st.session_state[answer_key] = ""
    else:
        st.warning("Keine Aufgaben gefunden. Bitte erstelle zuerst eine Aufgabe.")
>>>>>>> b6e1ea0f4313903e1659d9e4c9b406ec103080b6
