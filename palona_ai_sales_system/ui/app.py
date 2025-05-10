import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_workflow.welcome import welcome_section
from main_workflow.lead_selection import lead_selection
from main_workflow.sales_prep import sales_prep
from main_workflow.communication_summary import communication_summary
from main_workflow.email_draft import email_draft
from hubspot_db import hubspot_db
from login import login_page
from sidebar import sidebar

# Set wide mode for best reading experience
st.set_page_config(layout="wide")

# Custom CSS for background
st.markdown("""
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1428908728789-d2de25dbd4e2?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D');
        background-size: cover;
        background-position: center;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "Main Page"
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# Show login page if not authenticated
if not st.session_state["authenticated"]:
    login_page()
else:
    # Show sidebar for authenticated users
    sidebar()
    # Main content
    if st.session_state["page"] == "Main Page":
        welcome_section()
        if st.button("Get Started", key="get_started_btn"):
            st.session_state["page"] = "Lead Selection"
            st.rerun()
    elif st.session_state["page"] == "Lead Selection":
        lead_selection()
    elif st.session_state["page"] == "Sales Prep":
        sales_prep()
    elif st.session_state["page"] == "Communication Summary":
        communication_summary()
    elif st.session_state["page"] == "Message Drafting":
        email_draft()
    elif st.session_state["page"] == "HubSpot Database":
        hubspot_db()



