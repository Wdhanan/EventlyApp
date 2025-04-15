import streamlit as st
from sqlite3 import Error
from utils.database import create_connection


PRIMARY_COLOR = "#4A90E2"
SECONDARY_COLOR = "#F5F5F5"
ACCENT_COLOR = "#FFA500"
DARK_BG = "#1E1E1E"
DARK_CARD = "#2D2D2D"

# Custom CSS für modernes Login/Registrierung
AUTH_CSS = f"""
<style>
.auth-container {{
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}}

.dark-mode .auth-container {{
    background: #2D2D2D;
}}

.auth-title {{
    color: {PRIMARY_COLOR};
    text-align: center;
    margin-bottom: 1.5rem;
    font-size: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
}}

.auth-input {{
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    transition: all 0.3s ease;
}}

.dark-mode .auth-input {{
    background: #3A3A3A;
    border-color: #555;
    color: white;
}}

.auth-input:focus {{
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}}

.auth-button {{
    width: 100%;
    padding: 0.75rem;
    background-color: {PRIMARY_COLOR};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}}

.auth-button:hover {{
    background-color: #3a7bc8;
    transform: translateY(-2px);
}}

.auth-footer {{
    text-align: center;
    margin-top: 1.5rem;
    color: #777;
    font-size: 0.9rem;
}}

.dark-mode .auth-footer {{
    color: #AAA;
}}

.auth-link {{
    color: {PRIMARY_COLOR};
    text-decoration: none;
    cursor: pointer;
    font-weight: 500;
}}

.auth-logo {{
    text-align: center;
    margin-bottom: 1.5rem;
}}

/* Hide empty white block */
div[data-testid="stVerticalBlock"]:has(> div.element-container:empty) {{
    display: none;
}}
</style>
"""

def register():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)                
    
    
    st.markdown(f'<h2 class="auth-title">{("event")} Registrieren</h2>', unsafe_allow_html=True)
    
    with st.form(key='register_form'):
        username = st.text_input("Benutzername", key="register_username")
        password = st.text_input("Passwort", type="password", key="register_password")
        confirm_password = st.text_input("Passwort bestätigen", type="password", key="confirm_password")
        
        if st.form_submit_button(f"{('user-plus')} Konto erstellen", use_container_width=True):
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
                    except Error as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("Benutzername bereits vergeben.")
                        else:
                            st.error(f"Fehler bei der Registrierung: {e}")
                    finally:
                        conn.close()
    
    st.markdown('<div class="auth-footer">Bereits registriert? <span class="auth-link" onclick="window.location=\'?nav=Login\'">Zum Login</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def login():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"]:has(> div.element-container:empty) {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True) 
    

    st.markdown(f'<h2 class="auth-title">{("login")} Einloggen</h2>', unsafe_allow_html=True)
    
    with st.form(key='login_form'):
        username = st.text_input("Benutzername", key="login_username")
        password = st.text_input("Passwort", type="password", key="login_password")
        
        if st.form_submit_button(f"{('sign-in')} Einloggen", use_container_width=True):
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
    
    st.markdown('<div class="auth-footer">Noch kein Konto? <span class="auth-link" onclick="window.location=\'?nav=Registrierung\'">Registrieren</span></div>', unsafe_allow_html=True)
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