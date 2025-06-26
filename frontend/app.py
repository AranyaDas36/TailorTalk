import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests
from mycalendar.calendar_local import get_free_slots, book_event

st.set_page_config(page_title="TailorTalk AI Booking Agent")
st.title("🤖 My AI Agent")

# Example prompts and keywords for user reference
with st.expander("💡 Example prompts and keywords (click to expand)", expanded=True):
    st.markdown("""
    **You can try prompts like:**
    - Book a meeting for tomorrow afternoon
    - Schedule a call tomorrow at 3pm
    - Book a meeting on Friday at 5pm
    - I want to schedule a meeting for 27th June at 5pm
    - Book a slot for me next Monday at 2pm
    - Do I have any free time this Friday?
    - Am I available tomorrow afternoon?
    - Check my availability for today between 2-4pm
    - What time slots are free next week?
    
    **Keywords:**
    - book, schedule, meeting, call, availability, free time, available
    """)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "context" not in st.session_state:
    st.session_state["context"] = {}

backend_url = "https://tailortalk-pspc.onrender.com/chat"

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