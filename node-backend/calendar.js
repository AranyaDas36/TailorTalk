const fs = require('fs');
const path = require('path');
const { parseISO, isBefore, isAfter, addMinutes, formatISO } = require('date-fns');

const BOOKINGS_FILE = path.join(__dirname, 'mycalendar', 'bookings.json');

// Helper to read bookings
function readBookings() {
  if (!fs.existsSync(BOOKINGS_FILE)) return [];
  return JSON.parse(fs.readFileSync(BOOKINGS_FILE, 'utf-8'));
}

// Helper to write bookings
function writeBookings(bookings) {
  fs.writeFileSync(BOOKINGS_FILE, JSON.stringify(bookings, null, 2));
}

// Check if slot is free
function isSlotFree(start, end) {
  const bookings = readBookings();
  return !bookings.some(b =>
    isBefore(parseISO(b.start), end) && isAfter(parseISO(b.end), start)
  );
}

// Book event
function bookEvent(start, end, summary = "Meeting via TailorTalk") {
  const bookings = readBookings();
  if (!isSlotFree(start, end)) {
    return { status: "error", message: "Slot already booked" };
  }
  const event = {
    id: `evt_${Date.now()}`,
    summary,
    description: "",
    start: formatISO(start, { representation: 'complete' }),
    end: formatISO(end, { representation: 'complete' }),
  };
  bookings.push(event);
  writeBookings(bookings);
  return { status: "success", event_id: event.id };
}

// Suggest next free slot (finds next 1-hour slot after requested)
function suggestNextFreeSlot(start, end) {
  let tryStart = new Date(start);
  let tryEnd = new Date(end);
  for (let i = 0; i < 24; i++) {
    tryStart = addMinutes(tryStart, 60);
    tryEnd = addMinutes(tryEnd, 60);
    if (isSlotFree(tryStart, tryEnd)) {
      return { start: formatISO(tryStart), end: formatISO(tryEnd) };
    }
  }
  return null;
}

module.exports = { isSlotFree, bookEvent, suggestNextFreeSlot }; 