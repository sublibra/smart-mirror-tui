"""Calendar card for displaying upcoming Google Calendar events from iCal feed."""

from datetime import datetime, timedelta
from typing import Optional

import httpx
from icalendar import Calendar
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class CalendarCard(Card):
    """Calendar card displaying upcoming events from Google Calendar iCal feed."""

    DEFAULT_CSS = """
    #calendar Static {
        text-align: left;
        padding: 1;
    }

    #calendar .calendar-title {
        text-style: bold;
        color: white;
    }
    """

    # Event type icons (customize based on event patterns)
    EVENT_ICONS = {
        "meeting": "🗓️",
        "call": "📞",
        "lunch": "🍽️",
        "birthday": "🎂",
        "travel": "✈️",
        "workout": "💪",
        "doctor": "🏥",
        "default": "📅",
    }

    def __init__(
        self,
        config: Optional[CardConfig] = None,
        ical_url: str = "",
        max_events: int = 3,
    ):
        """Initialize the calendar card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            ical_url: Google Calendar iCal URL
            max_events: Maximum number of upcoming events to display
        """
        if config is None:
            config = CardConfig(
                name="Calendar",
                position=CardPosition.TOP_RIGHT,
                update_interval=300,  # Update every 5 minutes
                width=40,
                height=12,
                border_style="green",
                text_align="left",
            )
        super().__init__(config)
        self.ical_url = ical_url
        self.max_events = max_events
        self._events: list = []
        self._error_message = "Loading..."
        self._calendar_widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the calendar display."""
        self._calendar_widget = Static("Loading calendar...", classes="calendar-title")
        yield self._calendar_widget

    def _get_event_icon(self, summary: str) -> str:
        """Get icon based on event summary keywords.

        Args:
            summary: Event summary/title

        Returns:
            Appropriate icon emoji
        """
        summary_lower = summary.lower()

        # Check for keywords in summary
        for keyword, icon in self.EVENT_ICONS.items():
            if keyword in summary_lower:
                return icon

        return self.EVENT_ICONS["default"]

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for display.

        Args:
            dt: Datetime object

        Returns:
            Formatted time string
        """
        now = datetime.now(dt.tzinfo)

        # If today, show time
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M')}"

        # If tomorrow, show "Tomorrow"
        elif dt.date() == (now + timedelta(days=1)).date():
            return f"Tomorrow {dt.strftime('%H:%M')}"

        # Otherwise show day and time
        else:
            return dt.strftime("%a %b %d, %H:%M")

    def _format_calendar(self) -> str:
        """Format calendar events for display."""
        if self._error_message and self._error_message != "Loading...":
            return f"[bold red]Calendar Error[/bold red]\n{self._error_message}"

        if not self._events:
            return "[bold]📅  Calendar[/bold]\n\nNo upcoming events"

        lines = []
        # lines.append("[bold]📅  Upcoming Events[/bold]")
        # lines.append("")

        for i, event in enumerate(self._events[: self.max_events]):
            icon = event.get("icon", "📅")
            summary = event.get("summary", "Untitled Event")
            start = event.get("start")

            if start:
                time_str = self._format_time(start)
                # First event is bold, rest are gray
                if i == 0:
                    lines.append(f"[bold]{icon} {summary}[/bold]")
                    lines.append(f"[white]   {time_str}[/white]")
                else:
                    lines.append(f"[dim]{icon} {summary}[/dim]")
                    lines.append(f"[dim]   {time_str}[/dim]")

                # Add spacing between events (except after last)
                if i < len(self._events[: self.max_events]) - 1:
                    lines.append("")

        return "\n".join(lines)

    def _parse_ical_events(self, ical_data: str) -> list:
        """Parse iCal data and extract upcoming events.

        Args:
            ical_data: iCal format string

        Returns:
            List of event dicts sorted by start time
        """
        try:
            cal = Calendar.from_ical(ical_data)
            events = []
            now = datetime.now()

            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get("dtstart")
                    summary = component.get("summary")

                    if start and summary:
                        # Handle different datetime formats
                        start_dt = start.dt
                        if isinstance(start_dt, datetime):
                            # Make timezone-aware if naive
                            if start_dt.tzinfo is None:
                                from datetime import timezone

                                start_dt = start_dt.replace(tzinfo=timezone.utc)
                        else:
                            # If it's just a date, convert to datetime at midnight
                            from datetime import timezone

                            start_dt = datetime.combine(start_dt, datetime.min.time())
                            start_dt = start_dt.replace(tzinfo=timezone.utc)

                        # Only include future events
                        if start_dt.replace(tzinfo=None) >= now.replace(tzinfo=None):
                            events.append(
                                {
                                    "summary": str(summary),
                                    "start": start_dt,
                                    "icon": self._get_event_icon(str(summary)),
                                }
                            )

            # Sort by start time
            events.sort(key=lambda x: x["start"])
            return events

        except Exception as e:
            self.log(f"Error parsing iCal data: {e}", level="error")
            return []

    async def update(self) -> None:
        """Fetch calendar data from iCal URL."""
        if not self.ical_url:
            self._error_message = "No iCal URL configured"
            if self._calendar_widget:
                self._calendar_widget.update(self._format_calendar())
            return

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.ical_url)
                response.raise_for_status()
                ical_data = response.text

                self._events = self._parse_ical_events(ical_data)
                self._error_message = ""

        except httpx.HTTPError as e:
            self._error_message = f"HTTP Error: {str(e)[:30]}"
            self.log(f"HTTP error fetching calendar: {e}", level="error")
        except Exception as e:
            self._error_message = f"Error: {str(e)[:30]}"
            self.log(f"Error fetching calendar: {e}", level="error")

        # Update widget
        if self._calendar_widget:
            self._calendar_widget.update(self._format_calendar())
