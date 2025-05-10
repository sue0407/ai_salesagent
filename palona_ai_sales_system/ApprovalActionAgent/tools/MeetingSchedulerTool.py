from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class MeetingSchedulerTool(BaseTool):
    """
    Schedules a meeting with a prospect using Google Calendar API only.
    Accepts lead info, meeting details, and timezone (from LinkedInResearchTool output).
    Uses LLM-based action detection for consistency with MessageActionTool.
    """
    lead_email: str = Field(..., description="Email of the prospect to invite")
    lead_name: str = Field(..., description="Name of the prospect")
    meeting_subject: str = Field(..., description="Subject of the meeting")
    meeting_body: str = Field(..., description="Body/agenda of the meeting")
    start_time: str = Field(..., description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    duration_minutes: int = Field(default=30, description="Duration of the meeting in minutes")
    timezone: str = Field(default="UTC", description="Timezone for the meeting (e.g., 'America/Los_Angeles')")

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

    def _schedule_google(self):
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import base64
            import pickle
            from email.mime.text import MIMEText
            import os.path

            SCOPES = ["https://www.googleapis.com/auth/calendar"]
            creds = None
            token_path = "calendar_token.pickle"
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

            service = build('calendar', 'v3', credentials=creds)
            start = self.start_time
            end_dt = datetime.fromisoformat(start) + timedelta(minutes=self.duration_minutes)
            end = end_dt.isoformat()
            event = {
                'summary': self.meeting_subject,
                'description': self.meeting_body,
                'start': {'dateTime': start, 'timeZone': self.timezone},
                'end': {'dateTime': end, 'timeZone': self.timezone},
                'attendees': [{'email': self.lead_email, 'displayName': self.lead_name}],
                'conferenceData': {'createRequest': {'requestId': f"palona-{datetime.now().timestamp()}"}},
            }
            created_event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
            return {
                "status": "success",
                "platform": "google",
                "event_link": created_event.get('htmlLink'),
                "meet_link": created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', None)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run(self):
        """
        Schedules a meeting using Google Calendar API only.
        """
        return self._schedule_google()

