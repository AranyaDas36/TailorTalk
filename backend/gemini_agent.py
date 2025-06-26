import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    # Try to extract JSON from the response
    try:
        # Find the first { ... } block in the response
        start = response.text.find('{')
        end = response.text.rfind('}') + 1
        json_str = response.text[start:end]
        return json.loads(json_str)
    except Exception:
        return {
            "intent": None,
            "clarification_needed": True,
            "clarification_question": "Sorry, I couldn't understand your request. Please try again."
        } 