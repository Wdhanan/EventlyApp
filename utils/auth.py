import streamlit as st
from sqlite3 import Error
from utils.database import create_connection
from utils.database import create_tables

def init_db():
    """Initialisiert die Datenbank beim ersten Start"""
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/eventmanager.db"):
        create_tables()

# More professional color scheme
PRIMARY_COLOR = "#4A90E2"
SECONDARY_COLOR = "#F5F5F5"
ACCENT_COLOR = "#FFA500"
TEXT_COLOR = "#333333"
DARK_BG = "#1E1E1E"
DARK_CARD = "#2D2D2D"

def register():
    init_db()
    # Professional styling for the form - improved to reduce white space
    st.markdown("""
    <style>
    /* Clean up white blocks and force better styling */
    [data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
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
    }
    
    /* Form title with reduced margin */
    .auth-form-title {
        color: #333;
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
        color: #555 !important;
        margin-bottom: 3px !important;
    }
    
    /* Style inputs */
    .stTextInput input {
        background-color: #f8f9fa !important;
        border: 1px solid #ddd !important;
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
        background-color: #4A90E2 !important;
        color: white !important;
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
        background-color: #3a7bc8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Footer text with reduced margin */
    .auth-footer {
        text-align: center;
        margin-top: 15px;
        color: #777;
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

def login():
    init_db()
    # Professional styling for the form - improved to reduce white space
    st.markdown("""
    <style>
    /* Clean up white blocks and force better styling */
    [data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
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
        color: #333;
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
        color: #555 !important;
        margin-bottom: 3px !important;
    }
    
    /* Style inputs */
    .stTextInput input {
        background-color: #f8f9fa !important;
        border: 1px solid #ddd !important;
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
        background-color: #4A90E2 !important;
        color: white !important;
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
        background-color: #3a7bc8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Footer text with reduced margin */
    .auth-footer {
        text-align: center;
        margin-top: 15px;
        color: #777;
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
    st.markdown('<h2 class="auth-form-title">Willkommen zurück</h2>', unsafe_allow_html=True)
    
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
                        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", 
                                       (username, password))
                        user = cursor.fetchone()
                        if user:
                            st.session_state["logged_in"] = True
                            st.session_state["user_id"] = user[0]
                            st.session_state["username"] = username
                            st.success("Erfolgreich eingeloggt!")
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
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()
        st.success("Erfolgreich ausgeloggt.")

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
