from unittest.mock import patch, MagicMock
import utils.database
import sqlite3
import pytest
import os

TEST_DB_PATH = "data/test_eventmanager.db"
utils.database.DB_PATH = TEST_DB_PATH  

from utils.database import create_connection, create_tables
from utils.auth import register, login, get_user_premium_status_and_quiz_limits
from utils.event_manager import create_event, load_events, share_event
from utils.task_manager import save_task, load_tasks
from utils.event_stats_manager import save_stats, load_stats

@pytest.fixture(scope="module")
def test_db():
    """Fixture für die Test-Datenbank"""
    # Setze den Standard-Datenbankpfad auf die Testdatenbank
    utils.database.DB_PATH = TEST_DB_PATH
    # Jetzt legt create_tables() die Tabellen in der Testdatenbank an
    create_tables()
    conn = sqlite3.connect(TEST_DB_PATH)
    yield conn
    conn.close()
    try:
        os.remove(TEST_DB_PATH)
    except:
        pass
    
@pytest.fixture
def test_user(test_db):
    """Fixture für einen Test-Benutzer"""
    cursor = test_db.cursor()
    # Benutzer anlegen
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 ("testuser", "testpass"))
    test_db.commit()
    user_id = cursor.lastrowid
    yield user_id
    # Benutzer löschen
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    test_db.commit()

def test_create_and_load_events(test_db, test_user):
    """Testet das Erstellen und Laden von Events"""
    event_title = "Test Event"
    event_desc = "Test Beschreibung"
    event_id = create_event(test_user, event_title, event_desc)
    assert event_id is not None
    events = load_events(test_user)
    assert len(events) == 1
    assert events[0][1] == event_title
    assert events[0][2] == event_desc

def test_task_management(test_db, test_user):
    """Testet das Erstellen und Laden von Tasks"""
    event_id = create_event(test_user, "Task Test Event", "")
    task_title = "Test Task"
    task_content = "Test Inhalt"
    save_task(event_id, task_title, task_content)
    tasks = load_tasks(event_id)
    assert len(tasks) == 1
    assert tasks[0][1] == task_title
    assert tasks[0][2] == task_content

def test_user_authentication():
    """Testet die Benutzerauthentifizierung"""
    mock_st = MagicMock()
    mock_cookies = MagicMock()
    mock_st.session_state = {}
    with patch('utils.auth.st', mock_st), \
         patch('utils.auth.create_connection') as mock_conn:
        mock_conn.return_value = MagicMock()
        cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = cursor
        cursor.fetchone.return_value = (1, 0)  # user_id, is_premium
        login(mock_cookies)
        assert mock_st.session_state["logged_in"] is True
        assert mock_st.session_state["user_id"] == "1"
        assert mock_st.session_state["username"] == "testuser"

def test_stats_tracking(test_db, test_user):
    """Testet das Speichern und Laden von Statistiken"""
    event_id = create_event(test_user, "Stats Test Event", "")
    task_id = 1  
    save_stats(test_user, event_id, task_id, 85)
    stats = load_stats(test_user, event_id)
    assert len(stats) == 1
    assert stats[0][1] == 85  # Score

def test_premium_status_check(test_db, test_user):
    """Testet die Abfrage des Premium-Status"""
    is_premium, daily_count, last_reset = get_user_premium_status_and_quiz_limits(test_user)
    assert is_premium is False
    assert daily_count == 0
    assert last_reset is None

def test_event_sharing(test_db, test_user):
    """Testet das Teilen von Events"""
    cursor = test_db.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  ("shareuser", "sharepass"))
    test_db.commit()
    share_user_id = cursor.lastrowid
    event_id = create_event(test_user, "Share Test Event", "")
    share_event(event_id, test_user, "shareuser")
    cursor.execute("""
        SELECT COUNT(*) FROM shared_events 
        WHERE event_id = ? AND shared_with_user_id = ?
    """, (event_id, share_user_id))
    count = cursor.fetchone()[0]
    assert count == 1
    cursor.execute("DELETE FROM users WHERE id = ?", (share_user_id,))
    test_db.commit()

def test_database_connection():
    """Testet die Datenbankverbindung"""
    conn = create_connection() 
    assert conn is not None
    conn.close()