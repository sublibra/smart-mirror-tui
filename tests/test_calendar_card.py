"""Tests for the Calendar card."""

from datetime import datetime, timedelta, timezone

import pytest

from smart_mirror.plugins.base import CardPosition
from smart_mirror.plugins.calendar import CalendarCard


@pytest.mark.asyncio
async def test_calendar_card_compose():
    """Test calendar card composition."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")
    widgets = list(card.compose())
    assert len(widgets) == 1
    assert card._calendar_widget is not None


@pytest.mark.asyncio
async def test_calendar_card_no_url():
    """Test calendar card with no URL configured."""
    card = CalendarCard(ical_url="")
    list(card.compose())
    await card.update()
    assert "Ingen kalender-URL konfigurerad" in card._error_message


def test_calendar_card_event_icons():
    """Test event icon selection."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")

    assert card._get_event_icon("Team meeting") == "🗓️"
    assert card._get_event_icon("Call with client") == "📞"
    assert card._get_event_icon("Lunch break") == "🍽️"
    assert card._get_event_icon("Birthday party") == "🎂"
    assert card._get_event_icon("Travel to Paris") == "✈️"
    assert card._get_event_icon("Workout session") == "💪"
    assert card._get_event_icon("Doctor appointment") == "🏥"
    assert card._get_event_icon("Random event") == "📅"


def test_calendar_card_format_time():
    """Test time formatting."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")
    now = datetime.now(timezone.utc)

    # Today
    today_time = now.replace(hour=14, minute=30)
    formatted = card._format_time(today_time)
    assert "Idag" in formatted
    assert "14:30" in formatted

    # Tomorrow
    tomorrow_time = now + timedelta(days=1)
    formatted = card._format_time(tomorrow_time)
    assert "Imorgon" in formatted

    # Future date
    future_time = now + timedelta(days=5)
    formatted = card._format_time(future_time)
    assert "Idag" not in formatted
    assert "Imorgon" not in formatted


def test_calendar_card_parse_ical_basic():
    """Test basic iCal parsing."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")

    # Create a simple iCal data with a future date
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
DTSTART:20270205T140000Z
DTEND:20270205T150000Z
SUMMARY:Test Meeting
END:VEVENT
END:VCALENDAR"""

    events = card._parse_ical_events(ical_data)
    assert len(events) == 1
    assert events[0]["summary"] == "Test Meeting"
    assert "icon" in events[0]


def test_calendar_card_parse_ical_filters_past_events():
    """Test that past events are filtered out."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")

    # Create iCal with past event
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
DTSTART:20200101T140000Z
DTEND:20200101T150000Z
SUMMARY:Past Event
END:VEVENT
END:VCALENDAR"""

    events = card._parse_ical_events(ical_data)
    assert len(events) == 0


def test_calendar_card_parse_ical_sorts_by_time():
    """Test that events are sorted by start time."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")

    # Create iCal with multiple future events
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
DTSTART:20270203T140000Z
DTEND:20270203T150000Z
SUMMARY:Second Event
END:VEVENT
BEGIN:VEVENT
DTSTART:20270202T140000Z
DTEND:20270202T150000Z
SUMMARY:First Event
END:VEVENT
BEGIN:VEVENT
DTSTART:20270204T140000Z
DTEND:20270204T150000Z
SUMMARY:Third Event
END:VEVENT
END:VCALENDAR"""

    events = card._parse_ical_events(ical_data)
    assert len(events) == 3
    assert events[0]["summary"] == "First Event"
    assert events[1]["summary"] == "Second Event"
    assert events[2]["summary"] == "Third Event"


def test_calendar_card_max_events():
    """Test that max_events limits the display."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics", max_events=2)

    # Create multiple events
    card._events = [
        {"summary": "Event 1", "start": datetime.now(timezone.utc), "icon": "📅"},
        {
            "summary": "Event 2",
            "start": datetime.now(timezone.utc) + timedelta(hours=1),
            "icon": "📅",
        },
        {
            "summary": "Event 3",
            "start": datetime.now(timezone.utc) + timedelta(hours=2),
            "icon": "📅",
        },
    ]

    formatted = card._format_calendar()
    assert "Event 1" in formatted
    assert "Event 2" in formatted
    assert "Event 3" not in formatted


def test_calendar_card_position_default():
    """Test default card position."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")
    assert card.config.position == CardPosition.MIDDLE_RIGHT


def test_calendar_card_empty_events():
    """Test display with no events."""
    card = CalendarCard(ical_url="https://example.com/calendar.ics")
    card._events = []

    formatted = card._format_calendar()
    assert "Inga kommande händelser" in formatted
