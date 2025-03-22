import os
import json
import logging
import re
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from utils.task_manager import load_tasks, load_shared_tasks
from utils.event_stats_manager import save_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Configuration API
api_key = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Verzeichnis für Fragen
QUESTIONS_DIR = "data/questions"
os.makedirs(QUESTIONS_DIR, exist_ok=True)

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
            f"Generiere Fragen basierend auf den folgenden Aufgaben eines Events. Die Fragen sollten offen sein und aktives Lernen fördern.\n"
            f"Für jede Frage gib ein JSON-Objekt mit zwei Schlüsseln zurück: 'frage' für die Frage und 'antwort' für die korrekte Antwort.\n"
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
            f"Du bist ein Lehrer, der die Antwort eines Schülers bewertet.\n"
            f"Frage: {question}\n"
            f"Korrekte Antwort: {correct_answer}\n"
            f"Antwort des Schülers: {user_answer}\n\n"
            f"Bewertungsregeln:\n"
            f"- Kurze Antworten mit den wesentlichen Elementen verdienen eine hohe Punktzahl.\n"
            f"- Wenn die Schlüsselwörter vorhanden sind, sollte die Punktzahl hoch sein (4 oder 5).\n"
            f"- Die Form der Antwort ist weniger wichtig als der Inhalt.\n\n"
            f"Gib NUR ein gültiges JSON im folgenden Format zurück: {{\"score\": X}}, wobei X eine Zahl zwischen 0 und 5 ist.\n"
            f"Verwende doppelte Anführungszeichen für den Schlüssel \"score\"."
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

        return {"score": evaluation["score"]}

    except Exception as e:
        logging.exception("Fehler bei der Bewertung der Antwort: %s", e)
        return {"score": 0}

def quiz_mode(user_id, event_id):
    """
    Quiz-Modus für ein bestimmtes Event.
    :param user_id: Die ID des Benutzers
    :param event_id: Die ID des Events
    """
    st.header("Rätsel-Modus")
    tasks = load_tasks(event_id)
    shared_tasks = load_shared_tasks(user_id)
    all_tasks = tasks + shared_tasks  # Kombiniere eigene und geteilte Tasks

    if all_tasks:
        event_title = st.session_state.get("selected_event_title", "Event")
        selected_task = st.selectbox("Wähle eine Aufgabe", [task[1] for task in all_tasks], key="quiz_select_task")
        
        # Zurücksetzen der Fragen und Antworten, wenn eine neue Aufgabe ausgewählt wird
        if "selected_task" not in st.session_state or st.session_state["selected_task"] != selected_task:
            st.session_state["selected_task"] = selected_task
            st.session_state["questions"] = None
            st.session_state["answers"] = {}
            st.session_state["quiz_finished"] = False  # Zurücksetzen des Quiz-Status

        if st.button("Fragen generieren", key="generate_questions_button"):
            # Finde den vollständigen Task (id, title, content) für die ausgewählte Aufgabe
            selected_task_full = next(task for task in all_tasks if task[1] == selected_task)
            questions = generate_questions(event_title, [selected_task_full])  # Übergebe den vollständigen Task
            
            if questions:
                st.session_state["questions"] = questions  # Speichere die Fragen im session_state
                st.session_state["answers"] = {}  # Initialisiere die Antworten
                st.session_state["quiz_finished"] = False  # Quiz-Status zurücksetzen
            else:
                st.error("Es wurden keine Fragen generiert.")

        if "questions" in st.session_state and st.session_state["questions"]:
            st.write("Generierte Fragen:")
            questions = st.session_state["questions"]
            total_score = 0  # Gesamtpunktzahl für diese Quiz-Session
            all_answered = True  # Prüfe, ob alle Fragen beantwortet wurden

            for i, question in enumerate(questions, start=1):
                st.write(f"**Frage {i}:** {question['frage']}")
                
                # Antwortfeld mit session_state verknüpfen
                answer_key = f"user_answer_{i}"
                if answer_key not in st.session_state:
                    st.session_state[answer_key] = ""  # Initialisiere die Antwort
                
                # Textfeld für die Antwort
                user_answer = st.text_input(
                    f"Deine Antwort auf Frage {i}",
                    value=st.session_state[answer_key],  # Verwende den gespeicherten Wert
                    key=f"input_{answer_key}"  # Eindeutiger Schlüssel für das Widget
                )
                
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

                    # Speichere die Statistik, wenn alle Fragen beantwortet wurden
                    save_stats(user_id, event_id, total_score)
                    st.success("Quiz abgeschlossen! Deine Statistik wurde gespeichert.")
                    st.session_state["quiz_finished"] = True  # Markiere das Quiz als abgeschlossen

                    # Leere die Antwortfelder nach dem Abschluss des Quiz
                    for i in range(1, len(questions) + 1):
                        answer_key = f"user_answer_{i}"
                        st.session_state[answer_key] = ""
    else:
        st.warning("Keine Aufgaben gefunden. Bitte erstelle zuerst eine Aufgabe.")