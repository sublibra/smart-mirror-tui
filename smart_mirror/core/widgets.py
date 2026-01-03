"""Textual widgets for Smart Mirror cards."""

from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import Container
from rich.panel import Panel

from smart_mirror.plugins.base import Card


class CardWidget(Container):
    """Container widget that holds a Card's widgets."""
    
    def __init__(self, card: Card, **kwargs):
        """Initialize the card widget.
        
        Args:
            card: The Card instance to wrap
        """
        super().__init__(**kwargs)
        self.card = card
        self.border_title = card.name if card.config.show_title else None
        if card.config.show_border:
            self.border = ("solid", card.config.border_style)
        else:
            self.border = None
    
    def compose(self) -> ComposeResult:
        """Compose the card's widgets."""
        yield from self.card.compose()
    
    async def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Set up refresh interval if card has update method
        if hasattr(self.card, 'update'):
            self.set_interval(self.card.config.update_interval, self._update_card)
    
    async def _update_card(self) -> None:
        """Call card's update method and refresh display."""
        try:
            await self.card.update()
            # Refresh all child widgets
            for widget in self.query("*"):
                if hasattr(widget, 'refresh'):
                    widget.refresh()
        except Exception as e:
            self.app.log.error(f"Error updating {self.card.name}: {e}")
