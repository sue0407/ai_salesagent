import streamlit as st

def welcome_section():
    st.markdown("""
        <style>
        .palona-welcome-title {
            font-size: 2.8rem;
            font-weight: 900;
            color: #222;
            margin-bottom: 1rem;
        }
        .palona-welcome-desc {
            font-size: 1.2rem;
            color: #444;
            margin-bottom: 2rem;
        }
        .palona-step-header {
            font-size: 1.7rem;
            font-weight: 700;
            margin-top: 2rem;
        }
        .palona-step-list {
            font-size: 1.7rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="palona-welcome-title">Hi, {st.session_state.get("current_user", "User")}!</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="palona-welcome-desc">
        <b>🚀 Welcome to the Palona AI Sales System!</b><br>
        This is your intelligent sales co-pilot. The AI Sales Agent connects directly with your HubSpot CRM to streamline lead engagement, generate high-quality communications, and guide you through the next best actions to close deals faster and smarter.
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="palona-step-header">🛠 How to Use (Step-by-Step Guide)</div>
        <ol class="palona-step-list">
            <li><b>📋 View & Select a Lead:</b> View new deals assigned to you and select a lead to research.</li>
            <li><b>🧠 Generate Sales Prep Guide:</b> Review the AI-generated sales preparation report and upload any communication documents for a summary.</li>
            <li><b>📩 Draft & Send Email:</b> Generate, edit, and send a personalized outreach email to your lead.</li>
        </ol>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    welcome_section() 