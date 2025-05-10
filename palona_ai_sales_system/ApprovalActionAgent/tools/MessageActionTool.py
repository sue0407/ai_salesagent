from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
from typing import Literal
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
import importlib.util

load_dotenv()

class MessageActionTool(BaseTool):
    """
    Executes approved message actions (send email, update CRM, schedule meeting, etc.).
    Reads message from a txt file, fetches recipient info from CRM, uses Gmail API by default, and uses LLM to extract next step.
    """
    message_file: str = Field(
        ..., description="Path to the message txt file (output of MessageDraftingTool.py)"
    )
    lead_id: str = Field(
        ..., description="Lead ID to fetch recipient info from CRM"
    )
    email_method: Literal["gmail_api", "smtp"] = Field(
        default="gmail_api",
        description="Method to send email: 'gmail_api' (default) or 'smtp' (fallback)"
    )
    platform: Literal["google", "outlook", "mock"] = Field(
        default="mock",
        description="Platform to use for meeting scheduling if needed"
    )

    def _read_message_file(self, file_path: str):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        subject = lines[0].replace('Subject:', '').strip()
        body = ''.join(lines[1:]).strip()
        return {"subject": subject, "body": body}

    def _get_recipient_info(self, lead_id: str):
        data_file = Path(__file__).parent.parent.parent / 'data' / 'crm_data.json'
        with open(data_file, 'r') as f:
            crm_data = json.load(f)
        lead = next((l for l in crm_data["crm_leads"] if l["record_id"] == lead_id), None)
        if not lead:
            raise ValueError(f"Lead with id {lead_id} not found.")
        return {
            "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}",
            "email": lead.get("email"),
            "lead_id": lead_id
        }

    def _send_email_gmail_api(self, message, recipient):
        try:
            import base64
            from email.mime.text import MIMEText
            from googleapiclient.discovery import build
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import pickle
            import os.path

            SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
            creds = None
            token_path = "token.pickle"
            creds_path = os.getenv("GMAIL_API_CREDENTIALS")
            # Load token if it exists
            if os.path.exists(token_path):
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)
            # If no valid creds, do the OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the token for next time
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

            service = build('gmail', 'v1', credentials=creds)
            mime_msg = MIMEText(message["body"])
            mime_msg["to"] = recipient["email"]
            mime_msg["from"] = os.getenv("FROM_EMAIL", recipient["email"])
            mime_msg["subject"] = message["subject"]
            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
            body = {"raw": raw}
            service.users().messages().send(userId="me", body=body).execute()
            return True
        except Exception as e:
            raise Exception(f"Error sending email via Gmail API: {str(e)}")

    def _send_email_smtp(self, message, recipient):
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import smtplib
            smtp_config = self._get_smtp_config()
            if not all([smtp_config["username"], smtp_config["password"], smtp_config["from_email"]]):
                raise ValueError("SMTP configuration incomplete")
            msg = MIMEMultipart()
            msg["From"] = smtp_config["from_email"]
            msg["To"] = recipient["email"]
            msg["Subject"] = message["subject"]
            msg.attach(MIMEText(message["body"], "plain"))
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            
            raise Exception(f"Error sending email: {str(e)}")

    def _get_smtp_config(self):
        return {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("FROM_EMAIL")
        }

    def _llm_extract_next_step(self, message_body: str) -> str:
        # Use OpenAI/Claude to classify the next action
        import openai
        import os
        prompt = f"Given the following email, what is the next action for the sales rep? (send_email, schedule_meeting, follow_up, etc.)\nEmail:\n{message_body}\nAction:(return only the action label (e.g. send_email, schedule_meeting, follow_up, etc.))"
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            import anthropic
            client = anthropic.Anthropic(api_key=claude_key)
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=20,
                temperature=0,
                system="You are a helpful assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip().split("\n")[0]
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            client = openai.OpenAI(api_key=openai_key)
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0
            )
            return completion.choices[0].message.content.strip().split("\n")[0]
        return "send_email"

    def _update_crm(self, sent_message: str, lead_id: str, sent_date: str, next_follow_up: str = None):
        # Dynamically import CRMUpdateTool
        tool_path = Path(__file__).parent.parent.parent / 'CRMSyncAgent' / 'tools' / 'CRMUpdateTool.py'
        spec = importlib.util.spec_from_file_location("CRMUpdateTool", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        CRMUpdateTool = getattr(module, "CRMUpdateTool")
        tool = CRMUpdateTool(
            record_id=lead_id,
            email_message=sent_message,
            email_sent_date=sent_date,
            next_follow_up=next_follow_up
        )
        return tool.run()

    def _schedule_meeting(self, recipient, message):
        # Dynamically import MeetingSchedulerTool
        tool_path = Path(__file__).parent.parent / 'tools' / 'MeetingSchedulerTool.py'
        spec = importlib.util.spec_from_file_location("MeetingSchedulerTool", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        MeetingSchedulerTool = getattr(module, "MeetingSchedulerTool")
        start_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        tool = MeetingSchedulerTool(
            lead_email=recipient["email"],
            lead_name=recipient["name"],
            meeting_subject=message["subject"],
            meeting_body=message["body"],
            start_time=start_time,
            duration_minutes=30,
            platform=self.platform
        )
        return tool.run()

    def run(self):
        """
        Reads message from txt file, fetches recipient info, sends email (Gmail API default), updates CRM, and triggers meeting scheduling if needed.
        """
        try:
            # Read message and recipient
            message = self._read_message_file(self.message_file)
            recipient = self._get_recipient_info(self.lead_id)
            sent_date = datetime.now().strftime("%Y-%m-%d")
            # Send email
            if self.email_method == "gmail_api":
                success = self._send_email_gmail_api(message, recipient)
            else:
                success = self._send_email_smtp(message, recipient)
            # LLM extract next step
            next_action = self._llm_extract_next_step(message["body"])
            # Update CRM
            crm_update_result = self._update_crm(
                sent_message=message["body"],
                lead_id=self.lead_id,
                sent_date=sent_date,
                next_follow_up=""
            )
            # If next action is schedule_meeting, trigger meeting scheduler
            meeting_result = None
            if "schedule" in next_action or "meeting" in next_action or "call" in next_action:
                meeting_result = self._schedule_meeting(recipient, message)
            return json.dumps({
                "status": "success",
                "email_sent": success,
                "crm_update": crm_update_result,
                "next_action": next_action,
                "meeting_result": meeting_result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
