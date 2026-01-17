"""Textual widgets for Smart Mirror cards."""

from textual.app import ComposeResult
from textual.containers import Container

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
        if hasattr(self.card, "set_logger"):
            self.card.set_logger(self.log)
        # Call update immediately on mount
        if hasattr(self.card, "update"):
            # Devtools-friendly log
            self.log(f"Mounting {self.card.name} (interval={self.card.config.update_interval}s)")
            await self._update_card()
            # Then set up refresh interval for subsequent updates
            self.set_interval(self.card.config.update_interval, self._update_card)
        else:
            self.log(f"{self.card.name} mounted but no update method")

    async def _update_card(self) -> None:
        """Call card's update method and refresh display."""
        try:
            await self.card.update()
            # Update the last update timestamp
            from datetime import datetime

            self.card._last_update = datetime.now()
            # Refresh all child widgets
            for widget in self.query("*"):
                if hasattr(widget, "refresh"):
                    widget.refresh()
        except Exception as e:
            self.log(f"Error updating {self.card.name}: {type(e).__name__}: {e}")

            print(f"[CardWidget] Error updating {self.card.name}: {type(e).__name__}: {e}")
