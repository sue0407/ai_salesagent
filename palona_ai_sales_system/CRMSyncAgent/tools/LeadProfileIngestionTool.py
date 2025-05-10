from agency_swarm.tools import BaseTool
from pydantic import Field
import json
from pathlib import Path
import os
from datetime import datetime
import streamlit as st

class LeadProfileIngestionTool(BaseTool):
    """
    Tool for ingesting and managing lead profiles from the CRM system.
    This tool handles reading lead data and updating profiles. If selected_lead is provided, returns info for that lead; otherwise, returns all leads and deals.
    """
    selected_lead: str = Field(
        default=None,
        description="The selected lead in format 'First Last - Company'. If provided, returns info for this lead only. If not, returns all leads and deals."
    )

    def run(self):
        try:
            # Direct path to the CRM data file
            data_file = Path(__file__).parent.parent.parent / 'data' / 'crm_data.json'
            with open(data_file, 'r') as f:
                crm_data = json.load(f)

            if self.selected_lead:
                # Parse the selected lead string
                name_part, company_name = self.selected_lead.split(" - ")
                name_split = name_part.split(" ", 1)
                first_name = name_split[0]
                last_name = name_split[1] if len(name_split) > 1 else ""
                company_name = company_name.strip()

                # Find the matching lead (original logic)
                lead_info = None
                for lead in crm_data["crm_leads"]:
                    if (lead["first_name"].lower() == first_name.lower() and 
                        lead["last_name"].lower() == last_name.lower() and 
                        lead["company_name"].lower() == company_name.lower()):
                        lead_info = {
                            "lead_id": lead["record_id"],
                            "linkedin_url": lead.get("linkedin_url", ""),
                            "email": lead.get("email", ""),
                            "timezone": lead.get("timezone", "America/Los_Angeles"),
                            "first_name": lead["first_name"],
                            "last_name": lead["last_name"],
                            "company_name": lead["company_name"],
                            "job_title": lead.get("job_title", ""),
                            "phone": lead.get("phone", ""),
                            "lead_score": lead.get("lead_score", 0),
                            "customer_segment": lead.get("customer_segment", "")
                        }
                        break

                if not lead_info:
                    return {
                        "status": "error",
                        "message": f"Could not find lead information for {first_name} {last_name} at {company_name}"
                    }

                # Store in session state for reuse
                st.session_state["current_lead_info"] = lead_info
                return {
                    "status": "success",
                    "lead_info": lead_info
                }
            else:
                # Return all leads and deals
                return {
                    "status": "success",
                    "leads": crm_data["crm_leads"],
                    "deals": crm_data["deals"]
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error reading lead data: {str(e)}"
            }

