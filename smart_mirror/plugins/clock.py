"""Clock card for displaying current time."""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.widgets import Digits, Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class ClockCard(Card):
    """Large digital clock card positioned at the top center."""

    DEFAULT_CSS = """
    #clock {
        align: center top;
        layout: vertical;
    }

    #clock Digits {
        width: 100%;
        text-align: center;
        color: cyan;
    }
    #clock .date {
        width: 100%;
        text-align: center;
        text-style: none;
        color: $text-muted;
        color: cyan;
        padding-top: 0;
    }    """

    def __init__(self, config: Optional[CardConfig] = None):
        """Initialize the clock card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
        """
        if config is None:
            config = CardConfig(
                name="Clock",
                position=CardPosition.TOP_CENTER,
                update_interval=1,  # Update every second
                width=40,
                height=8,
                show_title=False,
                border_style="cyan",
            )
        super().__init__(config)
        self._current_time: Optional[datetime] = None
        self._digits_widget: Optional[Digits] = None
        self._date_widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the clock display."""
        self._digits_widget = Digits("")
        self._date_widget = Static("", classes="date")
        yield self._digits_widget
        yield self._date_widget

    async def update(self) -> None:
        """Update the current time and date display."""
        self._current_time = datetime.now()
        if self._digits_widget:
            time_str = self._current_time.strftime("%H:%M:%S")
            self._digits_widget.update(time_str)
        if self._date_widget:
            date_str = self._current_time.strftime("%A, %B %d, %Y")
            self._date_widget.update(date_str)
