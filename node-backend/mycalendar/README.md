# Local Calendar Integration

This project uses a local file-based calendar for booking and availability.

- All bookings are stored in `calendar/bookings.json`.
- No external accounts or APIs are required.
- Bookings persist after server restarts.

## How it works
- When you book a meeting, the event is saved to `bookings.json`.
- When you check availability, the system checks for conflicts in this file.

**No setup is required!** 