import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from CRMSyncAgent.tools.LeadProfileIngestionTool import LeadProfileIngestionTool
import pandas as pd

def lead_selection():
    st.subheader("Step 1: Select a Lead")
    st.markdown("""
    <b>Recent new leads assigned to you</b>  
    These are the most recent leads assigned to you, ordered by when they became a lead.  
    Please select one to proceed to the sales preparation guide.
    """, unsafe_allow_html=True)

    crm_tool = LeadProfileIngestionTool()
    result = crm_tool.run()
    if result["status"] != "success":
        st.error("Failed to load CRM data.")
        return
    leads = result["leads"]
    user = st.session_state.get("current_user", "Sue")
    user_leads = [lead for lead in leads if lead.get("sales_rep") == user]
    if not user_leads:
        st.info("No new leads assigned to you.")
        return
    # Sort by became_a_lead_date desc
    user_leads.sort(key=lambda x: x.get("became_a_lead_date", ""), reverse=True)
    display_cols = ["first_name", "last_name", "company_name", "job_title", "became_a_lead_date", "lead_score", "customer_segment"]
    df = pd.DataFrame(user_leads)[display_cols]

    # prettify column names
    df = df.rename(columns={
    "first_name": "First Name",
    "last_name": "Last Name",
    "company_name": "Company",
    "job_title": "Job Title",
    "became_a_lead_date": "Lead Date",
    "lead_score": "Lead Score",
    "customer_segment": "Customer Segment"
})
    # Reset index to avoid showing the index column
    df = df.reset_index(drop=True)

    st.dataframe(df, use_container_width=True)

    # Create a radio button for selection
    lead_options = [
    f"{row['First Name']} {row['Last Name']} - {row['Company']}"
    for _, row in df.iterrows()
]
    selected_lead = st.radio(
        "Select a lead to proceed:",
        lead_options,
        key="lead_radio"
    )

    # Consistent button style 
    if st.button("Proceed to Sales Prep Guide", key="proceed_sales_prep"):
        st.session_state["selected_lead"] = selected_lead
        # Set linkedin_url in session state using LeadProfileIngestionTool
        # Parse first and last name, company from selected_lead
        try:
            name_part, company_name = selected_lead.split(" - ")
            first_name, last_name = name_part.split(" ", 1)
            # Find the lead in the leads list
            lead = next((l for l in leads if l["first_name"] == first_name and l["last_name"] == last_name and l["company_name"] == company_name), None)
            if lead:
                st.session_state["linkedin_url"] = lead.get("linkedin_url", "")
            else:
                st.session_state["linkedin_url"] = ""
        except Exception:
            st.session_state["linkedin_url"] = ""
        st.session_state["page"] = "Sales Prep"
        st.rerun()

if __name__ == "__main__":
    lead_selection()