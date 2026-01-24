# Google Calendar Widget

The Calendar Card displays upcoming events from a Google Calendar via iCal feed.

## Features

- 📅 Shows the next X upcoming events (default: 3)
- 🎨 Similar look and feel to the Weather card
- 🔄 Auto-updates every 5 minutes
- 🎯 Smart icons based on event keywords
- 📍 Positioned at MIDDLE_RIGHT by default

## Configuration

Add to your `.env` file:

```bash
# Enable the calendar widget
ENABLE_CALENDAR=true

# Your Google Calendar iCal URL (required)
CALENDAR_ICAL_URL=https://calendar.google.com/calendar/ical/your-calendar-id/private-xxx/basic.ics

# Maximum number of events to display (optional, default: 3)
CALENDAR_MAX_EVENTS=3
```

## Getting Your Google Calendar iCal URL

1. Open [Google Calendar](https://calendar.google.com)
2. Click the **Settings** gear icon → **Settings**
3. In the left sidebar, click on the calendar you want to share
4. Scroll down to **Integrate calendar**
5. Copy the **Secret address in iCal format** URL
6. Paste it into your `.env` file as `CALENDAR_ICAL_URL`

⚠️ **Important**: Keep this URL private! Anyone with this URL can view your calendar events.

## Event Icons

The widget automatically selects icons based on event keywords:

| Keyword in Event Title | Icon | Example Event |
|------------------------|------|---------------|
| "meeting" | 🗓️ | "Team meeting" |
| "call" | 📞 | "Call with client" |
| "lunch" | 🍽️ | "Lunch break" |
| "birthday" | 🎂 | "Birthday party" |
| "travel" | ✈️ | "Travel to Paris" |
| "workout" | 💪 | "Workout session" |
| "doctor" | 🏥 | "Doctor appointment" |
| *(default)* | 📅 | Any other event |

## Display Format

Events are displayed with:
- **First event** in white/bold (most important)
- **Remaining events** in gray/dimmed
- **Time format**:
  - "Today HH:MM" for same-day events
  - "Tomorrow HH:MM" for next-day events
  - "Day Mon DD, HH:MM" for further future events

## Example Display

```
📅  Upcoming Events

🗓️  Team standup
   Today 09:00

📞  Call with client
   Today 14:30

🍽️  Lunch with Sarah
   Tomorrow 12:00
```

## Customization

You can customize the card by modifying [calendar.py](../smart_mirror/plugins/calendar.py):

- **Position**: Change `CardPosition.MIDDLE_RIGHT` to another position
- **Update interval**: Adjust `update_interval=300` (in seconds)
- **Card size**: Modify `width` and `height` values
- **Icons**: Add or modify entries in `EVENT_ICONS` dictionary
- **Max events**: Change default in constructor or via env variable

## CSS Styling

The calendar card uses the `#calendar` CSS selector. You can customize styling:

```css
#calendar Static {
    text-align: left;
    padding: 1;
}

#calendar .calendar-title {
    text-style: bold;
    color: white;
}
```

## Troubleshooting

### No events showing

- Check that your `CALENDAR_ICAL_URL` is correct
- Verify the calendar has future events
- Check that the iCal URL is the "Secret address" not the public URL
- Look at the logs for error messages

### Events not updating

- The card updates every 5 minutes by default
- You can force a refresh by restarting the app
- Check network connectivity

### Wrong timezone

- The widget uses the timezone from your calendar events
- Ensure your Google Calendar timezone settings are correct

## Technical Details

- **Library**: Uses `icalendar` for parsing iCal feeds
- **HTTP Client**: `httpx` with async support
- **Date Handling**: Native Python `datetime` with timezone support
- **Update Strategy**: Periodic polling (no webhooks)

## Future Enhancements

Potential improvements:
- Support for multiple calendars
- Event filtering by keywords
- Color coding by calendar or event type
- All-day event handling
- Event duration display
- Configurable date/time formats
