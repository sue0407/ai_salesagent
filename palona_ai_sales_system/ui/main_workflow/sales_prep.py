import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools_utils import run_tool, get_tool_inputs
from formatting_tool import ReportFormattingTool
from pathlib import Path

def sales_prep():
    st.subheader("Step 2: Sales Prep Guide")
    
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
        
    first_name, company_name = lead_parts[0], lead_parts[1]
    prospect_name = first_name

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

    # Initialize session state for research results
    if "company_research" not in st.session_state:
        st.session_state["company_research"] = None
    if "linkedin_research" not in st.session_state:
        st.session_state["linkedin_research"] = None
    if "sales_prep_generated" not in st.session_state:
        st.session_state["sales_prep_generated"] = False

    # Welcome message
    st.markdown(f"""
        <div class="palona-welcome-title">Sales Prep Guide for {prospect_name}</div>
        <div class="palona-welcome-desc">
            <b>Welcome to your personalized sales prep guide generator!</b><br>
            We'll help you prepare for your sales call with {prospect_name} at {company_name}.
        </div>
        <div class="palona-step-list">
            <b>Here's what we'll do:</b>
            <ol>
                <li>Research {company_name} to understand their business</li>
                <li>Research {prospect_name}'s LinkedIn profile for insights</li>
                <li>Generate a comprehensive sales prep guide</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)

    # Research Section
    st.markdown("### Research")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Company Research")
        if st.button("Research Company", key="company_research_btn"):
            with st.spinner("Researching company..."):
                result = run_tool("Company Research", {"company_name": company_name})
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["company_research"] = result["result"]
                    # Only show success message if not already generated
                    st.session_state["show_company_success"] = True
        
        if st.session_state["company_research"]:
            st.markdown("##### Company Research Results")
            st.text_area("", st.session_state["company_research"], height=800)
            st.session_state["show_company_success"] = False
        elif st.session_state.get("show_company_success"):
            st.success("Company research completed!")

    with col2:
        st.markdown("#### LinkedIn Research")
        linkedin_url = st.session_state.get("linkedin_url")
        if not linkedin_url:
            st.warning("LinkedIn URL not found. Please select a lead with LinkedIn information.")
        else:
            if st.button("Research Prospect", key="linkedin_research_btn"):
                with st.spinner("Researching prospect..."):
                    result = run_tool("LinkedIn Research", {
                        "linkedin_url": linkedin_url,
                        "name": prospect_name,
                        "company": company_name
                    })
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["linkedin_research"] = result["result"]
                        st.session_state["show_linkedin_success"] = True
        
        if st.session_state["linkedin_research"]:
            st.markdown("##### LinkedIn Research Results")
            st.text_area("", st.session_state["linkedin_research"], height=800)
            st.session_state["show_linkedin_success"] = False
        elif st.session_state.get("show_linkedin_success"):
            st.success("LinkedIn research completed!")

    # Generate Sales Prep Guide
    st.markdown("### Generate Sales Prep Guide")
    if not st.session_state["sales_prep_generated"]:
        st.markdown(f"""
            <div class="palona-welcome-desc">
                Click the button below to generate your personalized sales prep guide, or skip to the communication summary generator.
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Sales Prep Guide", use_container_width=True):
                if not st.session_state["company_research"] or not st.session_state["linkedin_research"]:
                    st.warning("Please complete both company and LinkedIn research first.")
                else:
                    with st.spinner("Generating your personalized sales prep guide..."):
                        result = run_tool("Report Generation", {
                            "company_name": company_name,
                            "prospect_name": prospect_name
                        })
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.session_state["sales_prep_report"] = result["result"]
                            st.session_state["sales_prep_generated"] = True
                            st.rerun()
        with col2:
            if st.button("Skip to Communication Summary", use_container_width=True):
                st.session_state["page"] = "Communication Summary"
                st.rerun()
    else:
        # Display the generated guide
        report = st.session_state["sales_prep_report"]
        
        # Format the report using the formatting tool
        formatting_tool = ReportFormattingTool(report_text=report)
        formatted_report = formatting_tool.run()
        
        # Display the formatted report
        st.markdown(formatted_report, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            # Download report button
            safe_company = company_name.replace(' ', '_').lower()
            safe_name = prospect_name.replace(' ', '_').lower()
            report_file = Path(__file__).parent.parent.parent / 'data' / 'outputs' / f'report_{safe_company}_{safe_name}.txt'
            if report_file.exists():
                with open(report_file, 'rb') as f:
                    st.download_button(
                        "Download Sales Prep Guide",
                        f,
                        file_name=report_file.name,
                        use_container_width=True
                    )
        with col2:
            if st.button("Proceed to Communication Summary", use_container_width=True):
                st.session_state["page"] = "Communication Summary"
                st.rerun()

if __name__ == "__main__":
    sales_prep()
