# TailorTalk Node Backend

This is the Node.js backend for TailorTalk, featuring Gemini API integration and file-based calendar booking.

## Setup

1. Install dependencies:
   ```sh
   npm install
   ```
2. Create a `.env` file in this folder:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
3. Ensure `mycalendar/bookings.json` exists and is writable.

## Running Locally

```sh
npm start
```

## Deployment (Render)
- Set the root directory to `node-backend`.
- Start command: `npm start`
- Add the environment variable `GEMINI_API_KEY` in the Render dashboard.

## Endpoints
- `GET /health` — Health check
- `POST /chat` — Conversational booking/chat endpoint 