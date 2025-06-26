import os
import json
from typing import List, Optional
from datetime import datetime, timedelta

BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "bookings.json")

def load_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []
    with open(BOOKINGS_FILE, "r") as f:
        return json.load(f)

def save_bookings(bookings):
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f)

def get_free_slots(start_time: datetime, end_time: datetime) -> List[str]:
    bookings = load_bookings()
    busy = []
    for event in bookings:
        event_start = datetime.fromisoformat(event["start"])
        event_end = datetime.fromisoformat(event["end"])
        if (start_time < event_end and end_time > event_start):
            busy.append({"start": event["start"], "end": event["end"]})
    return busy

def book_event(start_time: datetime, end_time: datetime, summary: str, description: Optional[str] = None):
    bookings = load_bookings()
    # Check for conflicts
    for event in bookings:
        event_start = datetime.fromisoformat(event["start"])
        event_end = datetime.fromisoformat(event["end"])
        if (start_time < event_end and end_time > event_start):
            return {"status": "conflict", "message": "Time slot is already booked."}
    new_event = {
        "id": f"evt_{int(datetime.now().timestamp())}",
        "summary": summary,
        "description": description or "",
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
    }
    bookings.append(new_event)
    save_bookings(bookings)
    return {"status": "success", "event_id": new_event["id"]}

def suggest_next_free_slot(start_time: datetime, end_time: datetime, duration_minutes: int = 60) -> Optional[dict]:
    """Suggest the next available free slot of given duration on the same day as start_time."""
    bookings = load_bookings()
    # Get all bookings for the same day
    day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    busy = [
        (datetime.fromisoformat(event["start"]), datetime.fromisoformat(event["end"]))
        for event in bookings
        if day_start <= datetime.fromisoformat(event["start"]) < day_end
    ]
    busy.sort()
    # Start searching from the requested start_time
    slot_start = start_time
    slot_end = slot_start + timedelta(minutes=duration_minutes)
    while slot_end <= day_end:
        conflict = False
        for b_start, b_end in busy:
            if slot_start < b_end and slot_end > b_start:
                conflict = True
                slot_start = b_end
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                break
        if not conflict:
            # Found a free slot
            return {"start": slot_start.isoformat(), "end": slot_end.isoformat()}
    return None 