const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const { parse, parseISO, addMinutes, format, isValid } = require('date-fns');
const chrono = require('chrono-node');
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
  let { message, context } = req.body;
  // Ensure context is always an array
  if (!Array.isArray(context)) context = [];
  try {
    // Build chat history for Gemini
    const history = context.map(msg =>
      ({ role: msg.sender === 'user' ? 'user' : 'model', parts: [{ text: msg.text }] })
    );
    history.push({ role: 'user', parts: [{ text: message }] });

    const model = genAI.getGenerativeModel({ model: 'models/gemini-2.0-flash' });
    const result = await model.generateContent({
      contents: history
    });

    const geminiResponse = result.response.text();

    // Add the new message to the context for future turns
    const newContext = [
      ...context,
      { sender: 'user', text: message },
      { sender: 'bot', text: geminiResponse }
    ];

    res.json({
      response: geminiResponse,
      context: newContext
    });
  } catch (error) {
    let msg = `Sorry, there was an error: ${error.message}`;
    if (error.message && error.message.includes('503')) {
      msg = "Sorry, the AI model is temporarily overloaded. Please try again in a few minutes.";
    }
    res.json({
      response: msg,
      context
    });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 