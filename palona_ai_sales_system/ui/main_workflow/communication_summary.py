import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools_utils import run_tool, get_tool_inputs
from formatting_tool import ReportFormattingTool
from pathlib import Path
from CRMSyncAgent.tools.LeadProfileIngestionTool import LeadProfileIngestionTool

def communication_summary():
    st.subheader("Step 3: Communication Summary")
    
    # Get selected lead info
    selected_lead = st.session_state.get("selected_lead")
    if not selected_lead:
        st.warning("Please select a lead first.")
        return
        
    # Parse lead info
    lead_parts = selected_lead.split(" - ")
    if len(lead_parts) < 2:
        st.error("Invalid lead selection.")
        return
        
    name_part, company_name = lead_parts[0], lead_parts[1]
    # Try to split name_part into first and last name
    name_split = name_part.split(" ", 1)
    first_name = name_split[0]
    last_name = name_split[1] if len(name_split) > 1 else ""
    prospect_name = first_name

    # Get the correct lead_id from CRM using LeadProfileIngestionTool
    crm_tool = LeadProfileIngestionTool()
    crm_result = crm_tool.run()
    lead_id = None
    if crm_result["status"] == "success":
        for lead in crm_result["leads"]:
            if lead["first_name"] == first_name and lead["company_name"] == company_name:
                lead_id = lead["record_id"]
                break
    if not lead_id:
        st.error("Could not find lead ID for selected lead.")
        return

    # Welcome message and guidance
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
        .palona-step-list {
            font-size: 1rem;
            color: #444;
            margin-bottom: 2rem;
        }
        .report-container {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 2rem 0;
        }
        .report-container h3 {
            color: #1E88E5;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-size: 1.4rem;
        }
        .report-container p {
            margin: 0.5rem 0;
            line-height: 1.6;
        }
        .report-container ul {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        .report-container li {
            margin: 0.3rem 0;
            line-height: 1.6;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "comm_summary_generated" not in st.session_state:
        st.session_state["comm_summary_generated"] = False
    if "communication_history" not in st.session_state:
        st.session_state["communication_history"] = None

    # Always fetch communication history for the selected lead
    if st.session_state["communication_history"] is None:
        result = run_tool("Communication History", {"lead_id": lead_id})
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state["communication_history"] = result["result"]

    # Document Upload and Summary Generation
    st.markdown("### Generate Communication Summary")
    if not st.session_state["comm_summary_generated"]:
        st.markdown(f"""
            <div class="palona-welcome-desc">
                Optionally upload any communication documents (emails, meeting notes, etc.) to enhance the summary of your interactions with {prospect_name} at {company_name}. If you don't upload, the summary will be generated based on CRM communication history only.
            </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload a communication document (txt, pdf, docx) (optional):",
            type=['txt', 'pdf', 'docx'],
            help="Upload any communication documents related to this lead (optional)"
        )

        uploaded_text = None
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                uploaded_text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                uploaded_text = " ".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                from docx import Document
                doc = Document(uploaded_file)
                uploaded_text = " ".join([p.text for p in doc.paragraphs])

        if st.button("Generate Communication Summary", use_container_width=True):
            # Generate summary based on uploaded_text if present, otherwise just CRM history
            with st.spinner("Generating communication summary..."):
                result = run_tool("Communication Summary", {
                    "lead_id": lead_id,
                    "uploaded_document": uploaded_text
                })
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["comm_summary_report"] = result["result"]
                    st.session_state["comm_summary_generated"] = True
                    st.rerun()
    else:
        comm_summary = st.session_state["comm_summary_report"]
        # Format the summary using the formatting tool
        formatting_tool = ReportFormattingTool(report_text=comm_summary)
        formatted_summary = formatting_tool.run()
        st.markdown(formatted_summary, unsafe_allow_html=True)
        
        # Download button for communication summary
        safe_company = company_name.replace(' ', '_').lower()
        safe_name = prospect_name.replace(' ', '_').lower()
        comm_file = Path(__file__).parent.parent.parent / 'data' / 'outputs' / f'comm_{safe_company}_{safe_name}.txt'
        # Save the summary to file if not already saved
        if not comm_file.exists():
            with open(comm_file, 'w') as f:
                f.write(comm_summary)
        if comm_file.exists():
            with open(comm_file, 'rb') as f:
                st.download_button(
                    "Download Communication Summary",
                    f,
                    file_name=comm_file.name,
                    use_container_width=True
                )
        # Action button
        if st.button("Proceed to Message Drafting", use_container_width=True):
            st.session_state["page"] = "Message Drafting"
            st.rerun()

if __name__ == "__main__":
    communication_summary() 