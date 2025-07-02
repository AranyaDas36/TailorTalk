import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests

st.set_page_config(page_title="TailorTalk AI Booking Agent")
st.title("🤖 My AI Agent")

# Add Clear Chat button
if st.button("Clear Chat"):
    st.session_state["messages"] = []
    st.session_state["context"] = {}
    st.rerun()

# Example prompts and keywords for user reference


if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "context" not in st.session_state:
    st.session_state["context"] = {}

backend_url = "https://tailortalk-node-backend.onrender.com/chat"


with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="input_box")
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        msg = user_input.strip()
        st.session_state["messages"].append(("user", msg))
        try:
            with st.spinner("Getting response..."):
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

# Show Clear Chat button at the bottom only if there are messages
if st.session_state["messages"]:
    if st.button("Clear Chat", key="clear_chat_bottom"):
        st.session_state["messages"] = []
        st.session_state["context"] = {}
        st.rerun() 