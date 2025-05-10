import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from CRMSyncAgent.tools.LeadProfileIngestionTool import LeadProfileIngestionTool
import pandas as pd
import json

def hubspot_db():
    st.header("HubSpot CRM & Deal Database")
    if st.button("Refresh CRM Data", use_container_width=True):
        st.session_state["refresh_crm"] = True
    # Always reload if refresh button is pressed
    crm_tool = LeadProfileIngestionTool()
    result = crm_tool.run()
    if result["status"] != "success":
        st.error("Failed to load CRM data.")
        return
    leads = result["leads"]
    deals = result["deals"]
    
    tab1, tab2 = st.tabs(["Leads", "Deals"])

    with tab1:
        st.subheader("Leads")
        df_leads = pd.DataFrame(leads)
        # Convert object columns to readable strings
        for col in df_leads.columns:
            if df_leads[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df_leads[col] = df_leads[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
        st.dataframe(df_leads, use_container_width=True)

    with tab2:
        st.subheader("Deals")
        df_deals = pd.DataFrame(deals)
        for col in df_deals.columns:
            if df_deals[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df_deals[col] = df_deals[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
        st.dataframe(df_deals, use_container_width=True)

if __name__ == "__main__":
    hubspot_db() 