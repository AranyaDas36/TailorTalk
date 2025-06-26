import re
from datetime import datetime, timedelta
import dateparser
from mycalendar.calendar_local import get_free_slots, book_event, suggest_next_free_slot
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests
import google.generativeai as genai
from backend.gemini_agent import extract_booking_info
import json

# Context will be passed as a dict (session) from the backend

# Set your Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_date_and_time(msg: str):
    dt = dateparser.parse(msg, settings={"PREFER_DATES_FROM": "future"})
    if not dt:
        return None, None, None
    # Try to find a time range (e.g., '3-5pm')
    range_match = re.search(r'(\d{1,2})\s*[-to]+\s*(\d{1,2}) ?pm', msg)
    if range_match:
        start_hour = int(range_match.group(1)) + 12
        end_hour = int(range_match.group(2)) + 12
        start = dt.replace(hour=start_hour, minute=0)
        end = dt.replace(hour=end_hour, minute=0)
        return start, end, True
    # If the time is exactly midnight (00:00) or 00:00:00, treat as missing
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return dt, None, False
    # If the user said 'now', treat as missing unless 'now' is in the message
    if (dt - datetime.now()).total_seconds() < 60 and 'now' not in msg:
        return dt, None, False
    # Otherwise, default to 1 hour meeting if no end time
    return dt, dt + timedelta(hours=1), True

# The context dict will be passed in and returned (for session state)
def process_user_message(message: str, context: dict = None):
    if context is None:
        context = {}
    info = extract_booking_info(message)
    # Clarification needed
    if info.get("clarification_needed"):
        return info.get("clarification_question", "Can you clarify your request?"), context
    # Booking intent
    if info.get("intent") == "book_meeting":
        date_str = info.get("date")
        time_str = info.get("time")
        duration = info.get("duration")
        if not date_str:
            return "What day would you like to book? (e.g., 'today', 'tomorrow', 'Friday')", context
        if not time_str:
            # Make the follow-up specific to the date
            try:
                date = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "future"})
            except Exception:
                date = None
            if date:
                if date.date() == datetime.now().date():
                    return "What time today would you like to book? (e.g., 2pm, 3pm, etc.)", context
                elif date.date() == (datetime.now() + timedelta(days=1)).date():
                    return "What time tomorrow would you like to book? (e.g., 2pm, 3pm, etc.)", context
                else:
                    return f"What time on {date.strftime('%A, %d %B %Y')} would you like to book? (e.g., 2pm, 3pm, etc.)", context
            else:
                return "What time would you like to book?", context
        # Parse date and time
        dt_str = f"{date_str} {time_str}"
        start = dateparser.parse(dt_str, settings={"PREFER_DATES_FROM": "future"})
        if not start:
            return "Sorry, I couldn't understand the date and time. Please try again.", context
        end = start + timedelta(hours=1)
        if duration:
            try:
                mins = int(duration)
                end = start + timedelta(minutes=mins)
            except Exception:
                pass
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
    if info.get("intent") == "check_availability":
        date_str = info.get("date")
        time_str = info.get("time")
        if not date_str:
            return "For which day should I check your availability? (e.g., 'Friday', 'today', 'tomorrow')", context
        if not time_str:
            try:
                date = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "future"})
            except Exception:
                date = None
            if date:
                if date.date() == datetime.now().date():
                    return "For what time today should I check your availability? (e.g., 2-4pm)", context
                elif date.date() == (datetime.now() + timedelta(days=1)).date():
                    return "For what time tomorrow should I check your availability? (e.g., 2-4pm)", context
                else:
                    return f"For what time on {date.strftime('%A, %d %B %Y')} should I check your availability? (e.g., 2-4pm)", context
            else:
                return "For what time should I check your availability?", context
        # Parse date and time
        dt_str = f"{date_str} {time_str}"
        start = dateparser.parse(dt_str, settings={"PREFER_DATES_FROM": "future"})
        if not start:
            return "Sorry, I couldn't understand the date and time. Please try again.", context
        end = start + timedelta(hours=1)
        busy = get_free_slots(start, end)
        if not busy:
            return (
                f"You are free from {start.strftime('%A, %d %B %Y at %I:%M %p')} to {end.strftime('%I:%M %p')}!",
                context
            )
        else:
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

def extract_booking_info(user_message, chat_history=None):
    prompt = f"""
You are a helpful AI assistant for booking meetings. Extract the user's intent, date, time, and any other details from the following message. If the message is ambiguous, ask a clarifying question.

User message: "{user_message}"

Return a JSON object with:
- intent: (book_meeting, check_availability, etc.)
- date: (ISO format or natural language)
- time: (if present)
- duration: (if present)
- clarification_needed: (true/false)
- clarification_question: (if needed)
"""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

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