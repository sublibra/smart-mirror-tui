"""Greeter card for personalized greetings."""

from datetime import datetime
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class GreeterCard(Card):
    """Greeter card that displays personalized greetings based on time of day."""
    
    DEFAULT_CSS = """
    #greeter Static {
        text-style: bold;
        color: orange;
        text-align: center;
        content-align: center middle;
    }
    """
    
    def __init__(self, config: Optional[CardConfig] = None, user_name: str = "there"):
        """Initialize the clock card.
        
        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            user_name: Name of the user to greet
        """
        if config is None:
            config = CardConfig(
                name="Greeter",
                position=CardPosition.MIDDLE_CENTER,
                update_interval=300,  # Update every 5 minutes
                width=35,
                height=8,
                show_border=False,
                show_title=False,
            )
        super().__init__(config)
        self._user_name = user_name
        self._greeting_widget: Optional[Static] = None
    
    def compose(self) -> ComposeResult:
        """Compose the greeting display."""
        self._greeting_widget = Static(self._get_greeting_text())
        yield self._greeting_widget
    
    def _get_greeting_text(self) -> str:
        """Get the current greeting text."""
        greeting = self._get_greeting()
        return f"{greeting}, {self._user_name}!"
    
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting.
        
        Returns:
            Greeting string based on current time
        """
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 22:
            return "Good evening"
        else:
            return "Good night"
    
    async def update(self) -> None:
        """Update the greeting text."""
        if self._greeting_widget:
            self._greeting_widget.update(self._get_greeting_text())
    
    def set_user_name(self, name: str) -> None:
        """Update the user name for greeting.
        
        Args:
            name: New user name
        """
        self._user_name = name
        if self._greeting_widget:
            self._greeting_widget.update(self._get_greeting_text())
