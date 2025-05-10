import streamlit as st
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MessageGenerationAgent.tools.MessageDraftingTool import MessageDraftingTool
from ApprovalActionAgent.tools.MessageActionTool import MessageActionTool
from CRMSyncAgent.tools.CRMUpdateTool import CRMUpdateTool
from pathlib import Path
from ApprovalActionAgent.tools.MeetingSchedulerTool import MeetingSchedulerTool
from CRMSyncAgent.tools.LeadProfileIngestionTool import LeadProfileIngestionTool
import datetime as dt

def email_draft():
    st.subheader("Step 4: Email Draft & Actions")
    selected_lead = st.session_state.get("selected_lead")
    if not selected_lead:
        st.warning("Please select a lead first.")
        return

    # Get lead information using the new function
    lead_tool = LeadProfileIngestionTool(selected_lead=selected_lead)
    result = lead_tool.run()
    
    if result.get("status") != "success":
        st.error(result.get("message", "Unknown error retrieving lead info."))
        st.write("Debug info:", result)  
        return

    lead_info = result.get("lead_info")
    if not lead_info:
        st.error("Lead information not found in CRM data.")
        st.write("Debug info:", result)  
        return
    lead_id = lead_info["lead_id"]
    prospect_name = lead_info["first_name"]
    company_name = lead_info["company_name"]
    recipient = lead_info["email"]

    st.markdown("""
        <style>
        .palona-welcome-title {
            font-size: 2.2rem;
            font-weight: 900;
            color: #222;
            margin-bottom: 1rem;
        }
        .palona-welcome-desc {
            font-size: 1.1rem;
            color: #444;
            margin-bottom: 1.5rem;
        }
        .palona-step-list {
            font-size: 1rem;
            color: #444;
            margin-bottom: 1.5rem;
        }
        .action-btn {
            margin-right: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div class="palona-welcome-title">Email Draft & Actions for {prospect_name}</div>
        <div class="palona-welcome-desc">
            <b>Welcome to your message drafting assistant!</b><br>
            Review and personalize your email draft to {prospect_name} at {company_name}. Use the action buttons below to send, save, or update CRM.
        </div>
    """, unsafe_allow_html=True)
    
    # Restore email draft generation logic
    if "email_draft_generated" not in st.session_state:
        st.session_state["email_draft_generated"] = False

    if not st.session_state["email_draft_generated"]:
        st.info("Click the button below to generate an email draft using AI.")
        if st.button("Generate Email Draft", use_container_width=True):
            with st.spinner("Generating email draft..."):
                draft_tool = MessageDraftingTool(company_name=company_name, prospect_name=prospect_name, lead_id=lead_id)
                result = draft_tool.run()
                if result["status"] != "success":
                    st.error("Failed to generate email draft.")
                    return
                message = result["message"]
                st.session_state["email_subject"] = message["subject"]
                st.session_state["email_body"] = message["body"]
                st.session_state["email_draft_generated"] = True
                st.rerun()
    else:
        # Email form
        with st.form("email_form"):
            to_val = st.text_input("To:", value=recipient, key="email_to")
            subject_val = st.text_input("Subject:", value=st.session_state.get("email_subject", ""), key="email_subject")
            body_val = st.text_area("Body:", value=st.session_state.get("email_body", ""), height=300, key="email_body")
            col1, col2 = st.columns(2)
            with col1:
                send = st.form_submit_button("Send Email")
            with col2:
                update_crm = st.form_submit_button("Update CRM")
        outputs_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs'
        outputs_dir.mkdir(parents=True, exist_ok=True)
        draft_file = outputs_dir / f'message_{company_name.replace(" ", "_").lower()}_{prospect_name.replace(" ", "_").lower()}.txt'
        if send:
            with open(draft_file, 'w') as f:
                f.write(f"Subject: {subject_val}\n\n{body_val}")
            action_tool = MessageActionTool(message_file=str(draft_file), lead_id=lead_id)
            action_result = action_tool.run()
            try:
                action_result_json = json.loads(action_result) if isinstance(action_result, str) else action_result
                if action_result_json.get("status") == "success":
                    st.success("Email sent!")
                    meeting_keywords = ["book", "schedule", "meeting", "call", "appointment", "follow_up"]
                    next_action = action_result_json.get("next_action", "").lower()
                    if any(word in next_action for word in meeting_keywords):
                        st.session_state["show_meeting_picker"] = True
                        st.session_state["meeting_picker_email_info"] = {
                            "recipient": to_val,
                            "prospect_name": prospect_name,
                            "company_name": company_name,
                            "subject": subject_val,
                            "body": body_val,
                            "lead_id": lead_id
                        }
                    else:
                        st.session_state["show_meeting_picker"] = False
                else:
                    st.error("Failed to send email: " + str(action_result))
            except Exception:
                st.error("Unexpected error: " + str(action_result))
        if update_crm:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            crm_tool = CRMUpdateTool(record_id=lead_id, email_message=body_val, email_sent_date=today)
            crm_result = crm_tool.run()
            try:
                crm_result_json = json.loads(crm_result) if isinstance(crm_result, str) else crm_result
                if crm_result_json.get("status") == "success":
                    st.success("CRM updated!")
                elif crm_result_json.get("status") == "no_update":
                    st.info("No fields updated in CRM (missing or empty info).")
                else:
                    st.error("CRM update failed: " + str(crm_result))
            except Exception:
                st.error("Unexpected CRM update result: " + str(crm_result))
        if st.session_state.get("show_meeting_picker"):
            st.info("The model suggests booking a meeting. Please select a date and time to schedule.")
            default_meeting_start = (dt.datetime.now() + dt.timedelta(days=1)).replace(second=0, microsecond=0)
            meeting_date = st.date_input(
                "Select meeting date:",
                value=default_meeting_start.date(),
                key="meeting_date_picker"
            )
            meeting_time = st.time_input(
                "Select meeting time:",
                value=default_meeting_start.time(),
                key="meeting_time_picker"
            )
            if st.button("Schedule Meeting", key="schedule_meeting_btn"):
                meeting_start_time = dt.datetime.combine(meeting_date, meeting_time)
                timezone = lead_info["timezone"]
                meeting_tool = MeetingSchedulerTool(
                    lead_email=lead_info["email"],
                    lead_name=prospect_name,
                    meeting_subject=subject_val,
                    meeting_body=body_val,
                    start_time=meeting_start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    duration_minutes=30,
                    timezone=timezone
                )
                meeting_result = meeting_tool.run()
                if meeting_result.get("status") == "success":
                    st.success(f"Meeting scheduled! Link: {meeting_result.get('event_link')}")
                    st.session_state["show_meeting_picker"] = False
                else:
                    st.error(f"Failed to schedule meeting: {meeting_result.get('message')}")

if __name__ == "__main__":
    email_draft() 