import datetime
import streamlit as st
from sqlite3 import Error
from utils.database import create_connection


# More professional color scheme
PRIMARY_COLOR = "#4A90E2"
SECONDARY_COLOR = "#F5F5F5"
ACCENT_COLOR = "#FFA500"
TEXT_COLOR = "#333333"
DARK_BG = "#1E1E1E"
DARK_CARD = "#2D2D2D"
dark_mode = st.session_state.get("dark_mode", False)

def register():

    st.markdown("""
    <style>
    /* Clean up white blocks and force better styling */
    [data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
        display: none !important;
    }
    /* Disable scrolling on auth pages */
    [data-testid="stAppViewContainer"] {
        background-color: {'#1E1E1E' if dark_mode else '#f5f7fa'} !important;
        overflow: hidden !important;
    }
    /* Hide scrollbar */
    ::-webkit-scrollbar {
        display: none !important;
    }
                
    /* Form container styling with reduced margins */
    .auth-form-container {
        background-color: {'#2D2D2D' if dark_mode else 'white'} !important;
        padding: 30px 40px;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        max-width: 420px;
        margin: 10px auto 30px;
        border-top: 5px solid #4A90E2;
        height: auto !important;
        min-height: unset !important;
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
    }
    
    /* Form title with reduced margin */
    .auth-form-title {
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
        text-align: center;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid {'#444' if dark_mode else '#eee'} !important;
    }
    
    /* Override input styling with reduced spacing */
    div[data-baseweb="input"] {
        margin-bottom: 15px !important;
    }
    
    /* Make labels bold and consistent */
    .stTextInput > label {
        font-weight: 600 !important;
        font-size: 14px !important;
        color: {TEXT_COLOR if dark_mode else '#555'} !important;
        margin-bottom: 3px !important;
    }
    
    /* Style inputs */
    .stTextInput input {
        background-color: {'#3A3A3A' if dark_mode else '#f8f9fa'} !important;
        border: 1px solid {'#555' if dark_mode else '#ddd'} !important;
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1) !important;
    }
    
    /* Button styling */
    .stButton > button {
       background-color: {ACCENT_COLOR} !important;
        color: {'#222' if dark_mode else 'white'} !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        margin-top: 5px !important;
    }
    
    .stButton > button:hover {
        background-color: {'#E69500' if dark_mode else '#3a7bc8'} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Footer text with reduced margin */
    .auth-footer {
        text-align: center;
        margin-top: 15px;
        color: {'#BBBBBB' if dark_mode else '#777'} !important;
        font-size: 14px;
    }
    
    /* Override background */
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa !important;
        background-image: none !important;
    }
    
    /* Override main content area to reduce empty space */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Fix empty space above forms */
    .st-emotion-cache-z5fcl4 {
        padding-top: 0 !important;
    }
    
    /* Hide empty blocks */
    .element-container:empty {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    st.markdown('<h2 class="auth-form-title">Neues Konto erstellen</h2>', unsafe_allow_html=True)
    
    with st.form("register_form_new"):
        username = st.text_input("Benutzername", key="reg_username_new")
        password = st.text_input("Passwort", type="password", key="reg_password_new")
        confirm_password = st.text_input("Passwort bestätigen", type="password", key="reg_confirm_new")
        
        submit = st.form_submit_button("Konto erstellen")
        
        if submit:
            if not username or not password:
                st.error("Benutzername und Passwort dürfen nicht leer sein.")
            elif password != confirm_password:
                st.error("Passwörter stimmen nicht überein!")
            else:
                conn = create_connection()
                if conn is not None:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                                       (username, password))
                        conn.commit()
                        st.success("Registrierung erfolgreich! Bitte melde dich jetzt an.")
                        st.session_state["show_login"] = True
                        st.session_state["show_register"] = False
                        st.rerun()
                    except Error as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("Benutzername bereits vergeben.")
                        else:
                            st.error(f"Fehler bei der Registrierung: {e}")
                    finally:
                        conn.close()
    
    st.markdown('<div class="auth-footer">Bereits registriert?</div>', unsafe_allow_html=True)
    if st.button("Zum Login", key="goto_login_new_btn"):
        st.session_state["show_login"] = True
        st.session_state["show_register"] = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def login(cookies):
    
    st.markdown("""
    <style>
    /* Clean up white blocks and force better styling */
    [data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
        display: none !important;
    }
                
    /* Disable scrolling on auth pages */
    [data-testid="stAppViewContainer"] {
        background-color: {'#1E1E1E' if dark_mode else '#f5f7fa'} !important;        
        overflow: hidden !important;
    }
    /* Hide scrollbar */
    ::-webkit-scrollbar {
        display: none !important;
    }
    
    /* Form container styling with reduced margins */
    .auth-form-container {
        background-color: white;
        padding: 30px 40px;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        max-width: 420px;
        margin: 10px auto 30px;
        border-top: 5px solid #4A90E2;
        height: auto !important;
        min-height: unset !important;
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
    }
    
    /* Logo styling with reduced margin */
    .auth-logo {
        text-align: center;
        margin-bottom: 15px;
    }
    
    .auth-logo img {
        width: 70px;
        height: auto;
    }
    
    /* Form title with reduced margin */
    .auth-form-title {
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
        text-align: center;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #eee;
    }
    
    /* Override input styling with reduced spacing */
    div[data-baseweb="input"] {
        margin-bottom: 15px !important;
    }
    
    /* Make labels bold and consistent */
    .stTextInput > label {
        font-weight: 600 !important;
        font-size: 14px !important;
        color: {TEXT_COLOR if dark_mode else '#555'} !important;
        margin-bottom: 3px !important;
    }
    
    /* Style inputs */
    .stTextInput input {
        background-color: {'#3A3A3A' if dark_mode else '#f8f9fa'} !important;
        border: 1px solid {'#555' if dark_mode else '#ddd'} !important;
        color: {TEXT_COLOR if dark_mode else '#333'} !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: {ACCENT_COLOR} !important;
        color: {'#222' if dark_mode else 'white'} !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        margin-top: 5px !important;
    }
    
    .stButton > button:hover {
        background-color: {'#E69500' if dark_mode else '#3a7bc8'} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Footer text with reduced margin */
    .auth-footer {
        text-align: center;
        margin-top: 15px;
        color: {'#BBBBBB' if dark_mode else '#777'} !important;
        font-size: 14px;
    }
    
    /* Override background */
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa !important;
        background-image: none !important;
    }
    
    /* Override main content area to reduce empty space */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Fix empty space above forms */
    .st-emotion-cache-z5fcl4 {
        padding-top: 0 !important;
    }
    
    /* Hide empty blocks */
    .element-container:empty {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    st.markdown('<div class="auth-logo"><img src="https://cdn-icons-png.flaticon.com/512/2476/2476589.png" alt="Logo"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-form-title">Welcome back!</h2>', unsafe_allow_html=True)
    
    with st.form("login_form_new"):
        username = st.text_input("Benutzername", key="login_username_new")
        password = st.text_input("Passwort", type="password", key="login_password_new")
        
        submit = st.form_submit_button("Einloggen")
        
        if submit:
            if username and password:
                conn = create_connection()
                if conn is not None:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, is_premium FROM users WHERE username = ? AND password = ?", 
                        (username, password))
                        user = cursor.fetchone()

                        if user:
                            user_id, is_premium = user
                            cookies["logged_in"] = "true"
                            cookies["user_id"] = str(user_id)
                            cookies["username"] = username
                            cookies["is_premium"] = str(is_premium)
                            cookies.save()

                            st.session_state.logged_in = True
                            st.session_state.user_id = str(user_id)
                            st.session_state.username = username
                            st.session_state.is_premium = bool(is_premium)
                            st.rerun()

                        else:
                            st.error("Ungültige Anmeldedaten.")
                    except Error as e:
                        st.error(f"Fehler beim Login: {e}")
                    finally:
                        conn.close()
            else:
                st.error("Benutzername und Passwort dürfen nicht leer sein.")
    
    st.markdown('<div class="auth-footer">Noch kein Konto?</div>', unsafe_allow_html=True)
    if st.button("Registrieren", key="goto_register_new_btn"):
        st.session_state["show_login"] = False
        st.session_state["show_register"] = True
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def logout():
    if "logged_in" in st.session_state:
        cookies = st.session_state.get("cookies")
        if cookies:
            cookies["logged_in"] = "false"
            cookies["user_id"] = ""
            cookies["username"] = ""
            cookies.save()
        st.session_state.logged_in = False  # <- wichtig!
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.show_login = True
        st.session_state.show_register = False
        st.rerun()
        st.success("Erfolgreich ausgeloggt.")
    

def update_profile(user_id, new_username=None, new_password=None):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if new_username:
                cursor.execute("UPDATE users SET username = ? WHERE id = ?", 
                             (new_username, user_id))
            if new_password:
                cursor.execute("UPDATE users SET password = ? WHERE id = ?",
                             (new_password, user_id))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Profilupdate fehlgeschlagen: {e}")
            return False
        finally:
            conn.close()        

def load_all_users():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users")
            users = cursor.fetchall()
            return [user[0] for user in users]
        except Error as e:
            st.error(f"Fehler beim Laden der Benutzer: {e}")
        finally:
            conn.close()
    return []


def get_user_premium_status_and_quiz_limits(user_id):
    """
    Ruft den Premium-Status, den täglichen Quiz-Zähler und das letzte Reset-Datum eines Benutzers ab.
    """
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_premium, daily_quiz_count, last_quiz_reset FROM users WHERE id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                is_premium, daily_quiz_count, last_quiz_reset = result
                return is_premium == 1, daily_quiz_count, last_quiz_reset
        except Error as e:
            st.error(f"Fehler beim Abrufen des Benutzerstatus: {e}")
        finally:
            conn.close()
    return False, 0, None

def update_user_quiz_count(user_id):
    """
    Aktualisiert den täglichen Quiz-Zähler eines Benutzers und setzt ihn gegebenenfalls zurück.
    """
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Aktuellen Status abrufen
            cursor.execute(
                "SELECT daily_quiz_count, last_quiz_reset, is_premium FROM users WHERE id = ?",
                (user_id,)
            )
            current_count, last_reset_str, is_premium = cursor.fetchone()

            today = datetime.now().date()
            last_reset_date = None
            if last_reset_str:
                try:
                    last_reset_date = datetime.fromisoformat(last_reset_str).date()
                except ValueError:
                    # Falls das Format nicht stimmt, setzen wir es zurück
                    last_reset_date = None 

            # Wenn der letzte Reset nicht heute war oder gar nicht gesetzt ist, oder wenn der Benutzer Premium ist,
            # aber der Zähler noch nicht zurückgesetzt wurde (z.B. nach Upgrade)
            if not last_reset_date or last_reset_date < today:
                new_count = 1
                new_reset_date_str = today.isoformat()
            else:
                new_count = current_count + 1
                new_reset_date_str = last_reset_str # Bleibt gleich

            cursor.execute(
                "UPDATE users SET daily_quiz_count = ?, last_quiz_reset = ? WHERE id = ?",
                (new_count, new_reset_date_str, user_id)
            )
            conn.commit()
            return new_count, True
        except Error as e:
            st.error(f"Fehler beim Aktualisieren des Quiz-Zählers: {e}")
            return None, False
        finally:
            conn.close()
    return None, False


def set_user_premium(username):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_premium = 1 WHERE username = ?", (username,))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Fehler beim Upgrade: {e}")
        finally:
            conn.close()
    return False
