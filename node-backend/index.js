const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const { parse, parseISO, addMinutes, format, isValid } = require('date-fns');
const { isSlotFree, bookEvent, suggestNextFreeSlot } = require('./calendar');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/chat', async (req, res) => {
  const { message, context } = req.body;
  try {
    // Use Gemini API to extract intent and details
    const model = genAI.getGenerativeModel({ model: 'models/gemini-2.0-flash' });
    const prompt = `
You are a helpful AI assistant for booking meetings. Extract the user's intent, date, time, and any other details from the following message.
If the message is ambiguous, do your best to guess, but set any missing fields to null and add a clarifying question.
Always return a valid JSON object with these fields:
- intent: (book_meeting, check_availability, etc.)
- date: (ISO 8601 format or null)
- time: (24h format 'HH:mm' or null)
- duration: (in minutes or null)
- clarification_needed: (true/false)
- clarification_question: (if needed, otherwise null)

User message: "${message}"
`;

    const result = await model.generateContent(prompt);
    const text = result.response.text();

    // Try to parse JSON from the response
    let info;
    try {
      const jsonStart = text.indexOf('{');
      const jsonEnd = text.lastIndexOf('}') + 1;
      info = JSON.parse(text.substring(jsonStart, jsonEnd));
    } catch (err) {
      return res.json({
        response: "Sorry, I couldn't understand the Gemini response.",
        context,
      });
    }

    // Clarification needed
    if (info.clarification_needed) {
      return res.json({
        response: info.clarification_question || "Can you clarify your request?",
        context,
      });
    }

    // Booking intent
    if (info.intent === 'book_meeting') {
      const dateStr = info.date;
      const timeStr = info.time;
      const duration = info.duration || 60; // default 60 mins

      if (!dateStr && !timeStr) {
        return res.json({ response: "What day and time would you like to book? (e.g., 'tomorrow at 2pm')", context });
      }
      if (!dateStr) {
        return res.json({ response: "What day would you like to book? (e.g., 'tomorrow', 'Friday', '27th June')", context });
      }
      if (!timeStr) {
        return res.json({ response: `What time on ${dateStr} would you like to book? (e.g., '2pm', '14:00')`, context });
      }

      // Parse date and time
      let start;
      try {
        start = parseISO(`${dateStr}T${timeStr}`);
        if (!isValid(start)) {
          // Try parsing as natural language
          start = parse(`${dateStr} ${timeStr}`, 'yyyy-MM-dd HH:mm', new Date());
        }
        if (!isValid(start)) throw new Error('Invalid time value');
      } catch {
        return res.json({ response: "Sorry, I couldn't understand the date and time. Please try again with a format like '27th June at 2pm' or 'tomorrow at 14:00'.", context });
      }
      const end = addMinutes(start, parseInt(duration));
      const result = bookEvent(start, end);

      if (result.status === "success") {
        return res.json({
          response: `Booked your meeting for ${format(start, 'PPpp')} to ${format(end, 'p')}! Event ID: ${result.event_id}`,
          context,
        });
      } else {
        const suggestion = suggestNextFreeSlot(start, end);
        if (suggestion) {
          return res.json({
            response: `Could not book: Time slot is already booked. Next available slot: ${format(parseISO(suggestion.start), 'PPpp')} to ${format(parseISO(suggestion.end), 'p')}. Would you like to book this?`,
            context,
          });
        } else {
          return res.json({
            response: "Could not book: Time slot is already booked and no free slots are available today.",
            context,
          });
        }
      }
    }

    // Availability intent
    if (info.intent === 'check_availability') {
      const dateStr = info.date;
      const timeStr = info.time;
      const duration = info.duration || 60;

      if (!dateStr && !timeStr) {
        return res.json({ response: "For which day and time should I check your availability? (e.g., 'Friday at 3pm')", context });
      }
      if (!dateStr) {
        return res.json({ response: "For which day should I check your availability? (e.g., 'Friday', 'tomorrow')", context });
      }
      if (!timeStr) {
        return res.json({ response: `For what time on ${dateStr} should I check your availability? (e.g., '2-4pm', '14:00')`, context });
      }

      let start;
      try {
        start = parseISO(`${dateStr}T${timeStr}`);
        if (!isValid(start)) {
          start = parse(`${dateStr} ${timeStr}`, 'yyyy-MM-dd HH:mm', new Date());
        }
        if (!isValid(start)) throw new Error('Invalid time value');
      } catch {
        return res.json({ response: "Sorry, I couldn't understand the date and time. Please try again with a format like '27th June at 2pm' or 'tomorrow at 14:00'.", context });
      }
      const end = addMinutes(start, parseInt(duration));
      if (isSlotFree(start, end)) {
        return res.json({
          response: `You are free from ${format(start, 'PPpp')} to ${format(end, 'p')}!`,
          context,
        });
      } else {
        const suggestion = suggestNextFreeSlot(start, end);
        if (suggestion) {
          return res.json({
            response: `You are busy at that time. Next available slot: ${format(parseISO(suggestion.start), 'PPpp')} to ${format(parseISO(suggestion.end), 'p')}.`,
            context,
          });
        } else {
          return res.json({
            response: "You are busy at that time and no free slots are available today.",
            context,
          });
        }
      }
    }

    // Fallback
    return res.json({
      response: "I'm here to help you with your calendar. Try asking to book a meeting or check availability!",
      context,
    });
  } catch (error) {
    // Handle Gemini API errors (including quota exceeded)
    if (
      error.message &&
      error.message.includes('ResourceExhausted')
    ) {
      return res.json({
        response: "You have exceeded your Gemini API quota. Please try again later.",
        context,
      });
    }
    return res.json({
      response: `Sorry, there was an error: ${error.message}`,
      context,
    });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 