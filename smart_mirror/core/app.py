"""Main Smart Mirror TUI application."""

import asyncio
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardPosition
from smart_mirror.plugins.clock import ClockCard
from smart_mirror.plugins.weather import WeatherCard
from smart_mirror.plugins.greeter import GreeterCard
from smart_mirror.core.widgets import CardWidget


class SmartMirrorApp(App):
    """Main application for the smart mirror TUI."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1 2;
        padding: 1 2;
        background: $surface;
    }
    
    CardWidget {
        width: 100%;
        height: 100%;
    }
    
    /* Position classes */
    .top-left { column-span: 1; row-span: 1; }
    .top-center { column-span: 1; row-span: 1; }
    .top-right { column-span: 1; row-span: 1; }
    .middle-left { column-span: 1; row-span: 1; }
    .middle-center { column-span: 1; row-span: 1; }
    .middle-right { column-span: 1; row-span: 1; }
    .bottom-left { column-span: 1; row-span: 1; }
    .bottom-center { column-span: 1; row-span: 1; }
    .bottom-right { column-span: 1; row-span: 1; }
    """
    
    def __init__(self):
        """Initialize the smart mirror application."""
        load_dotenv()
        self.cards: Dict[str, Card] = {}
        self.card_widgets: Dict[str, CardWidget] = {}
        
        # Initialize plugins first to collect their CSS
        self._initialize_plugins()
        
        # Build combined CSS from app + all cards
        self._build_combined_css()
        
        # Now initialize the Textual App with combined CSS
        super().__init__()
        
        # Load configuration from environment
        self.width = int(os.getenv("DISPLAY_WIDTH", "120"))
        self.height = int(os.getenv("DISPLAY_HEIGHT", "30"))
        self.refresh_rate = float(os.getenv("REFRESH_RATE", "1"))
    
    def _build_combined_css(self) -> None:
        """Combine app CSS with all card CSS."""
        card_css = []
        for card in self.cards.values():
            if hasattr(card, 'DEFAULT_CSS') and card.DEFAULT_CSS:
                card_css.append(card.DEFAULT_CSS)
        
        if card_css:
            # Combine base CSS with card CSS
            self.__class__.CSS = self.__class__.CSS + "\n" + "\n".join(card_css)
    
    def _initialize_plugins(self) -> None:
        """Initialize default plugins/cards."""
        # Initialize greeter card
        user_name = os.getenv("DEFAULT_USER_NAME", "there")
        greeter = GreeterCard(user_name=user_name)
        self.register_card(greeter)
        
        # Initialize clock card
        clock = ClockCard()
        self.register_card(clock)
        
        # Initialize weather card with coordinates from env
        latitude = float(os.getenv("WEATHER_LATITUDE", "52.5200"))
        longitude = float(os.getenv("WEATHER_LONGITUDE", "13.4050"))
        weather = WeatherCard(latitude=latitude, longitude=longitude)
        self.register_card(weather)
    
    def register_card(self, card: Card) -> None:
        """Register a card/plugin with the application.
        
        Args:
            card: Card instance to register
        """
        self.cards[card.name] = card
    
    def get_card(self, name: str) -> Optional[Card]:
        """Get a registered card by name.
        
        Args:
            name: Card name
            
        Returns:
            Card instance or None if not found
        """
        return self.cards.get(name)
    
    def set_user_name(self, name: str) -> None:
        """Update the greeter with a recognized user name.
        
        This will be called by the PIR sensor integration when a face is recognized.
        
        Args:
            name: Recognized user name
        """
        greeter = self.get_card("Greeter")
        if greeter and isinstance(greeter, GreeterCard):
            greeter.set_user_name(name)
    
    def compose(self) -> ComposeResult:
        """Create the UI layout with card widgets."""
        # Create a 3x3 grid for the 9 positions
        position_map = {
            CardPosition.TOP_LEFT: "top-left",
            CardPosition.TOP_CENTER: "top-center",
            CardPosition.TOP_RIGHT: "top-right",
            CardPosition.MIDDLE_LEFT: "middle-left",
            CardPosition.MIDDLE_CENTER: "middle-center",
            CardPosition.MIDDLE_RIGHT: "middle-right",
            CardPosition.BOTTOM_LEFT: "bottom-left",
            CardPosition.BOTTOM_CENTER: "bottom-center",
            CardPosition.BOTTOM_RIGHT: "bottom-right",
        }
        
        # Create widgets for each position
        grid_positions = {}
        for card in self.cards.values():
            if card.config.enabled:
                widget = CardWidget(card)
                # Add CSS ID based on card name (lowercase)
                widget.id = card.name.lower()
                # Add CSS class based on position
                css_class = position_map.get(card.position, "middle-center")
                widget.add_class(css_class)
                self.card_widgets[card.name] = widget
                grid_positions[card.position] = widget
        
        # Create placeholders for empty positions
        all_positions = list(CardPosition)
        for position in all_positions:
            if position not in grid_positions:
                widget = Static("", classes=position_map[position])
                grid_positions[position] = widget
        
        # Yield widgets in grid order
        for position in all_positions:
            yield grid_positions[position]
    
    async def on_mount(self) -> None:
        """Called when app is mounted - start card update loops."""
        # Start all card update tasks
        for card in self.cards.values():
            if card.config.enabled:
                await card.start()
    
    async def on_unmount(self) -> None:
        """Called when app is unmounting - stop all cards."""
        for card in self.cards.values():
            if card.is_running():
                await card.stop()


def main() -> None:
    """Main entry point for the application."""
    app = SmartMirrorApp()
    app.run()


if __name__ == "__main__":
    main()
