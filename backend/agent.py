import re
from datetime import datetime, timedelta
import dateparser
from mycalendar.calendar_local import get_free_slots, book_event, suggest_next_free_slot
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests

# Context will be passed as a dict (session) from the backend

def parse_time_from_message(msg: str):
    dt = dateparser.parse(msg, settings={"PREFER_DATES_FROM": "future"})
    if dt:
        # Try to find a time range (e.g., '3-5pm')
        range_match = re.search(r'(\d{1,2})\s*[-to]+\s*(\d{1,2}) ?pm', msg)
        if range_match:
            start_hour = int(range_match.group(1)) + 12
            end_hour = int(range_match.group(2)) + 12
            start = dt.replace(hour=start_hour, minute=0)
            end = dt.replace(hour=end_hour, minute=0)
            return start, end
        # Otherwise, default to 1 hour meeting if no end time
        return dt, dt + timedelta(hours=1)
    return None, None

# The context dict will be passed in and returned (for session state)
def process_user_message(message: str, context: dict = None):
    if context is None:
        context = {}
    msg = message.lower().strip()
    booking_keywords = ["book", "schedule", "meeting", "call"]
    yes_keywords = ["yes", "book this", "ok", "sure"]
    avail_keywords = ["free time", "availability", "available", "free", "busy"]

    # If user says yes and a suggested slot exists, book it
    if any(word == msg for word in yes_keywords) and context.get("suggested_slot"):
        slot = context.pop("suggested_slot")
        start = dateparser.parse(slot["start"])
        end = dateparser.parse(slot["end"])
        result = book_event(start, end, summary="Meeting via TailorTalk")
        if result["status"] == "success":
            return f"Booked your meeting for {start.strftime('%A, %d %B %Y at %I:%M %p')} to {end.strftime('%I:%M %p')}! Event ID: {result['event_id']}", context
        else:
            return f"Could not book: {result['message']}", context

    # Booking intent
    if any(word in msg for word in booking_keywords) or context.get("pending_booking"):
        start, end = parse_time_from_message(msg)
        if not start or not end:
            # Ask for missing time
            context["pending_booking"] = True
            if "afternoon" in msg:
                return "What time in the afternoon? (e.g., 2pm, 3pm, etc.)", context
            elif "morning" in msg:
                return "What time in the morning? (e.g., 9am, 10am, etc.)", context
            elif "evening" in msg:
                return "What time in the evening? (e.g., 6pm, 7pm, etc.)", context
            else:
                return "What day and time would you like to book? (e.g., '27th June at 5pm')", context
        context.pop("pending_booking", None)
        result = book_event(start, end, summary="Meeting via TailorTalk")
        if result["status"] == "success":
            return (
                f"Booked your meeting for {start.strftime('%A, %d %B %Y at %I:%M %p')} to {end.strftime('%I:%M %p')}! "
                f"Event ID: {result['event_id']}"
            , context)
        else:
            suggestion = suggest_next_free_slot(start, end)
            if suggestion:
                context["suggested_slot"] = suggestion
                sug_start = dateparser.parse(suggestion["start"]).strftime('%A, %d %B %Y at %I:%M %p')
                sug_end = dateparser.parse(suggestion["end"]).strftime('%I:%M %p')
                return (
                    f"Could not book: Time slot is already booked. "
                    f"Next available slot: {sug_start} to {sug_end}. Would you like to book this?",
                    context
                )
            else:
                return "Could not book: Time slot is already booked and no free slots are available today.", context

    # Availability intent
    if any(word in msg for word in avail_keywords) or context.get("pending_availability"):
        start, end = parse_time_from_message(msg)
        if not start or not end:
            context["pending_availability"] = True
            return "For which day/time should I check your availability? (e.g., 'Friday at 5pm' or 'today between 2-4pm')", context
        context.pop("pending_availability", None)
        busy = get_free_slots(start, end)
        if not busy:
            return (
                f"You are free from {start.strftime('%A, %d %B %Y at %I:%M %p')} to {end.strftime('%I:%M %p')}!",
                context
            )
        else:
            # Suggest a free slot after the busy period
            suggestion = suggest_next_free_slot(start, end)
            if suggestion:
                sug_start = dateparser.parse(suggestion["start"]).strftime('%A, %d %B %Y at %I:%M %p')
                sug_end = dateparser.parse(suggestion["end"]).strftime('%I:%M %p')
                return (
                    f"You are busy at that time. Next available slot: {sug_start} to {sug_end}.",
                    context
                )
            else:
                return "You are busy at that time and no free slots are available today.", context

    # Fallback
    return (
        "I'm here to help you with your calendar. Try asking to book a meeting or check availability!\n"
        "Example: 'Book a meeting for tomorrow afternoon' or 'Do I have any free time this Friday?'",
        context
    )

st.set_page_config(page_title="TailorTalk AI Booking Agent")
st.title("🤖 My AI Scheduler Agent")

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "context" not in st.session_state:
    st.session_state["context"] = {}

backend_url = "http://localhost:8000/chat"

st.write("Ask me to book a meeting, check your calendar, or find a free slot!")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="input_box")
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        msg = user_input.strip()
        st.session_state["messages"].append(("user", msg))
        try:
            resp = requests.post(backend_url, json={"message": msg, "context": st.session_state["context"]})
            if resp.ok:
                data = resp.json()
                bot_msg = data.get("response", "(No response from bot)")
                st.session_state["context"] = data.get("context", {})
            else:
                bot_msg = f"Sorry, there was an error: {resp.text}"
        except Exception as e:
            bot_msg = f"Error: {e}"
        st.session_state["messages"].append(("bot", bot_msg))

for sender, msg in st.session_state["messages"]:
    if sender == "user":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**TailorTalk:** {msg}") 