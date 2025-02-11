import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from logo import show_app_logo

def init_auth_db():
    """Initialize authentication database"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password TEXT NOT NULL,
                  email TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def show_login_page():
    """Show the login page"""
    show_app_logo()
    
    st.markdown("""
        <style>
        .terms-text {
            color: #808080;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_auth_db()
    
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Define terms and conditions text
    terms_text = """
    By checking this box, I agree to:
    1. Share my bank statement data with this application
    2. Allow the app to analyze my transaction history
    3. Store my transaction data securely
    4. Process my financial information for insights
    5. Understand that my data will be automatically deleted upon logout
    
    Your data will be used only for analysis purposes and will not be shared with third parties.
    All your data will be permanently deleted when you logout from the application.
    """
    
    if st.session_state.show_register:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_email = st.text_input("Email", key="reg_email")
        
        # Terms checkbox with hover help
        terms_accepted = st.checkbox(
            "I agree to process my data for analysis purposes and accept the terms of service",
            key="reg_terms",
            help=terms_text
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit"):
                if not terms_accepted:
                    st.error("Please accept the Terms and Conditions to register")
                    return
                    
                if register_user(reg_username, reg_password, reg_email):
                    st.success("Registration successful! Please login.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Username already exists")
        with col2:
            if st.button("Back to Login"):
                st.session_state.show_register = False
                st.rerun()
    else:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Terms checkbox with hover help
        terms_accepted = st.checkbox(
            "I agree to process my data for analysis purposes and accept the terms of service",
            key="login_terms",
            help=terms_text
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                if not terms_accepted:
                    st.error("Please accept the Terms and Conditions to login")
                    return
                    
                if check_credentials(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        with col2:
            if st.button("Register"):
                st.session_state.show_register = True
                st.rerun()

def register_user(username, password, email):
    """Register a new user"""
    try:
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                 (username, hashed_pw, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def check_credentials(username, password):
    """Check if username/password combination is valid"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    result = c.fetchone()
    conn.close()
    return result is not None

def logout_user():
    """Log out the current user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]