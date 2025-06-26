# Deprecated: Use calendar_local.py for local file-based calendar storage.

# calendar/google_calendar.py
import os
from typing import List, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def authenticate_google():
    """Authenticate and return a Google Calendar service client."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    service = build("calendar", "v3", credentials=creds)
    return service

def get_free_slots(service, start_time: datetime, end_time: datetime) -> List[str]:
    """Return a list of free time slots between start_time and end_time."""
    body = {
        "timeMin": start_time.isoformat() + "Z",
        "timeMax": end_time.isoformat() + "Z",
        "items": [{"id": "primary"}]
    }
    eventsResult = service.freebusy().query(body=body).execute()
    busy_times = eventsResult["calendars"]["primary"]["busy"]
    # For demo: just return busy slots, real logic would return free slots
    return busy_times

def book_event(service, start_time: datetime, end_time: datetime, summary: str, description: Optional[str] = None):
    """Book an event in the user's Google Calendar."""
    event = {
        "summary": summary,
        "description": description or "",
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return {"status": "success", "event_id": created_event["id"]} 