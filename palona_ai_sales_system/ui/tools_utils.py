import streamlit as st
from CRMSyncAgent.tools.SimilarDealsTool import SimilarDealsTool
from CRMSyncAgent.tools.LeadProfileIngestionTool import LeadProfileIngestionTool
from CRMSyncAgent.tools.CRMUpdateTool import CRMUpdateTool
from CRMSyncAgent.tools.CommunicationHistoryTool import CommunicationHistoryTool
from ResearchAgent.tools.ReportGenerationTool import ReportGenerationTool
from ResearchAgent.tools.LinkedInResearchTool import LinkedInResearchTool
from ResearchAgent.tools.CompanyResearchTool import CompanyResearchTool
from ResearchAgent.tools.CommunicationSummaryTool import CommunicationSummaryTool
import json

# Map tool names to classes and their input fields with descriptions
TOOLS = {
    "Similar Deals": {
        "class": SimilarDealsTool,
        "fields": {
            "industry": "Target industry to match against",
            "criteria": "Additional matching criteria (JSON format, e.g., {'deal_size': 100000})"
        }
    },
    "Lead Profile Ingestion": {
        "class": LeadProfileIngestionTool,
        "fields": {}
    },
    "CRM Update": {
        "class": CRMUpdateTool,
        "fields": {
            "record_id": "Lead record_id to update",
            "email_message": "Email message to log",
            "email_sent_date": "Date the email was sent (YYYY-MM-DD)",
            "next_follow_up": "Next follow-up date (YYYY-MM-DD, optional)"
        }
    },
    "Communication History": {
        "class": CommunicationHistoryTool,
        "fields": {
            "lead_id": "The ID of the lead to retrieve communication history for"
        }
    },
    "Report Generation": {
        "class": ReportGenerationTool,
        "fields": {
            "company_name": "Name of the company to generate report for",
            "prospect_name": "Full name of the prospect to generate report for"
        }
    },
    "LinkedIn Research": {
        "class": LinkedInResearchTool,
        "fields": {
            "linkedin_url": "LinkedIn profile URL to research",
            "name": "Full name of the person to research",
            "company": "Current company of the person to research"
        }
    },
    "Company Research": {
        "class": CompanyResearchTool,
        "fields": {
            "company_name": "Name of the company to research"
        }
    },
    "Communication Summary": {
        "class": CommunicationSummaryTool,
        "fields": {
            "lead_id": "Lead record_id to summarize communications for",
            "uploaded_document": "Text content of the user-uploaded communication document (optional)"
        }
    }
}

def get_input_widget(field_name, field_description):
    """Create appropriate input widget based on field name and description"""
    if field_name == "criteria":
        return st.text_area(field_description, value="{}", help="Enter JSON format criteria")
    elif field_name == "uploaded_document":
        return st.text_area(field_description, help="Paste communication document content here")
    elif "date" in field_name.lower():
        return st.date_input(field_description)
    else:
        return st.text_input(field_description)

def run_tool(tool_name, inputs):
    """Run a tool with the given inputs and return the result"""
    try:
        tool_info = TOOLS[tool_name]
        
        # Parse JSON input if present
        if "criteria" in inputs and inputs["criteria"]:
            try:
                inputs["criteria"] = json.loads(inputs["criteria"])
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format for criteria"}

        # Instantiate and run tool
        tool = tool_info["class"](**inputs)
        result = tool.run()
        return {"success": True, "result": result}

    except Exception as e:
        return {"error": str(e)}

def get_tool_inputs(tool_name):
    """Get input widgets for a specific tool"""
    tool_info = TOOLS[tool_name]
    inputs = {}
    for field_name, field_description in tool_info["fields"].items():
        inputs[field_name] = get_input_widget(field_name, field_description)
    return inputs 