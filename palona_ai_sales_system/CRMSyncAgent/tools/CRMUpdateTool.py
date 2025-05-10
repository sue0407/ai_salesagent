from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Robust path resolution for crm_data.json
CRM_DATA_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'crm_data.json')

class CRMUpdateTool(BaseTool):
    """
    Updates the mock CRM system (crm_data.json) after actions are taken.
    Adds to message_log, updates last_contact_date, next_follow_up, increments interaction_count, and handles missing info gracefully.
    """
    record_id: str = Field(
        ..., description="Lead record_id to update"
    )
    email_message: str = Field(
        default=None, description="Email message to log"
    )
    email_sent_date: str = Field(
        default=None, description="Date the email was sent (YYYY-MM-DD)"
    )
    next_follow_up: str = Field(
        default=None, description="Next follow-up date (YYYY-MM-DD, optional)"
    )

    def run(self):
        try:
            # Validate record_id
            if not self.record_id:
                return json.dumps({
                    "status": "error",
                    "message": "record_id is required"
                })
            # Path to crm_data.json
            data_file = CRM_DATA_PATH
            with open(data_file, 'r') as f:
                crm_data = json.load(f)
            updated = False
            found = False
            for lead in crm_data["crm_leads"]:
                if lead["record_id"] == self.record_id:
                    found = True
                    # Add to message_log and update last_contact_date only if both email_message and email_sent_date are provided
                    if self.email_message and self.email_sent_date:
                        if "message_log" not in lead or not isinstance(lead["message_log"], list):
                            lead["message_log"] = []
                        lead["message_log"].append({
                            "message": self.email_message,
                            "timestamp": self.email_sent_date
                        })
                        lead["last_contact_date"] = self.email_sent_date
                        updated = True
                        # Update next_follow_up if provided, else auto-calc
                        next_follow_up_val = self.next_follow_up
                        if not next_follow_up_val:
                            try:
                                dt = datetime.strptime(self.email_sent_date, "%Y-%m-%d")
                                next_dt = dt + timedelta(days=7)
                                next_follow_up_val = next_dt.strftime("%Y-%m-%d")
                            except Exception:
                                next_follow_up_val = None
                        if next_follow_up_val:
                            lead["next_follow_up"] = next_follow_up_val
                            updated = True
                    # If only next_follow_up is provided, update it
                    elif self.next_follow_up:
                        lead["next_follow_up"] = self.next_follow_up
                        updated = True
                    # Increment interaction_count if any update
                    if updated and "interaction_count" in lead:
                        lead["interaction_count"] = int(lead["interaction_count"]) + 1
                    break
            if not found:
                return json.dumps({
                    "status": "error",
                    "message": f"record_id {self.record_id} not found"
                })
            if updated:
                with open(data_file, 'w') as f:
                    json.dump(crm_data, f, indent=4)
                return json.dumps({
                    "status": "success",
                    "message": "Lead updated successfully",
                    "record_id": self.record_id
                })
            else:
                return json.dumps({
                    "status": "no_update",
                    "message": "No fields updated (missing or empty info)",
                    "record_id": self.record_id
                })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }) 