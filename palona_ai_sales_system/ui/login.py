import streamlit as st

def login_page():
    st.markdown("""
        <style>
        .login-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #222;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        .login-subtitle {
            font-size: 1.2rem;
            color: #444;
            margin-bottom: 2rem;
            text-align: center;
        }
        .stButton>button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
            padding: 0.5rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        div[data-testid="stForm"] {
            background-color: rgba(255, 255, 255, 0.9);
            padding: 2.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: 0 auto;
        }
        div[data-testid="stForm"] > div {
            width: 100%;
        }
        div[data-testid="stForm"] input {
            width: 100%;
            padding: 0.75rem;
            font-size: 1.1rem;
        }
        div[data-testid="stForm"] label {
            font-size: 1.1rem;
            font-weight: 500;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-title">Welcome Back</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Sign in to your Palona AI Sales System account</div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        remember = st.checkbox("Remember Me")
        login_btn = st.form_submit_button("Sign in now")
        
        if login_btn:
            if username == "Sue" and password == "12345":
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password.")

if __name__ == "__main__":
    login_page() 