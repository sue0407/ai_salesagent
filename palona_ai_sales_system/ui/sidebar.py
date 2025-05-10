import streamlit as st

def sidebar():
    st.sidebar.title("Palona AI Sales System")
    if "current_user" in st.session_state:
        st.sidebar.markdown(f"**User:** {st.session_state['current_user']}")
    page = st.sidebar.radio(
        "Navigation",
        ["Main Page", "Lead Selection", "Sales Prep", "Communication Summary", "Message Drafting", "HubSpot Database"],
        index=["Main Page", "Lead Selection", "Sales Prep", "Communication Summary", "Message Drafting", "HubSpot Database"].index(st.session_state["page"])
    )
    st.session_state["page"] = page
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    sidebar() 