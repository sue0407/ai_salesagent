from agency_swarm.tools import BaseTool
from pydantic import Field
import json
from pathlib import Path
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CommunicationHistoryTool(BaseTool):
    """
    Tool for managing and retrieving communication history for leads.
    This tool handles reading communication-related fields from the CRM data file.
    """
    
    lead_id: str = Field(
        ...,
        description="The ID of the lead to retrieve communication history for"
    )
    
    def run(self):
        """
        Retrieve communication-related fields for the specified lead, including notes, last contact date, interaction count, preferred contact method, timezone, and message log.
        """
        try:
            # Direct path to the CRM data file
            data_file = Path(__file__).parent.parent.parent / 'data' / 'crm_data.json'
            
            # Read the CRM data
            with open(data_file, 'r') as f:
                crm_data = json.load(f)
            
            # Get lead information
            lead = next((l for l in crm_data["crm_leads"] if l["record_id"] == self.lead_id), None)
            if not lead:
                return {
                    "status": "error",
                    "message": f"Lead with ID {self.lead_id} not found"
                }
            
            # Fetch communication-related fields
            communication_info = {
                "notes": lead["notes"],
                "last_contact_date": lead["last_contact_date"],
                "interaction_count": lead["interaction_count"],
                "preferred_contact_method": lead["preferred_contact_method"],
                "timezone": lead["timezone"],
                "message_log": lead["message_log"]
            }
            
            return {
                "status": "success",
                "lead_id": self.lead_id,
                "lead_info": {
                    "name": f"{lead['first_name']} {lead['last_name']}",
                    "company": lead["company_name"],
                    "title": lead["job_title"],
                    "status": lead["status"],
                    "lead_score": lead["lead_score"]
                },
                "communication_info": communication_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving communication history: {str(e)}"
            } 