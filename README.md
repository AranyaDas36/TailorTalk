# TailorTalk

A conversational AI agent that helps users book appointments on their Google Calendar through a natural chat interface.

## Features
- Conversational agent for booking and checking calendar availability
- Google Calendar integration
- Chat interface with Streamlit
- Backend API with FastAPI
- Agent logic with LangGraph

## Tech Stack
- **Backend:** Python, FastAPI
- **Agent:** LangGraph
- **Frontend:** Streamlit
- **Calendar:** Google Calendar API

## Setup Instructions

1. **Clone the repository**
2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up Google Calendar API credentials**
   - Follow the instructions in the `calendar/README.md` (to be created) to set up OAuth2 credentials.
5. **Run the backend**
   ```bash
   uvicorn backend.main:app --reload
   ```
6. **Run the frontend**
   ```bash
   streamlit run frontend/app.py
   ```

## Example Conversations
- "Hey, I want to schedule a call for tomorrow afternoon."
- "Do you have any free time this Friday?"
- "Book a meeting between 3-5 PM next week."

---

## Project Structure
- `backend/` — FastAPI backend and agent logic
- `frontend/` — Streamlit chat interface
- `calendar/` — Google Calendar integration 