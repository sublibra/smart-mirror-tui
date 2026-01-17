""" Getting Qlik Menu for the coming week """

from datetime import datetime
from typing import Optional
import httpx
from textual.app import ComposeResult
from textual.widgets import Static
import logging

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class QlikMenuCard(Card):
    """ Get the Qlik Menu for the coming week """
    
    DEFAULT_CSS = """
    #qlik_menu Static {
        text-style: bold;
        color: orange;
        text-align: center;
        content-align: center middle;
    }
    """
    
    def __init__(self, config: Optional[CardConfig] = None, processing_server_location: str = ""):
        """Initialize the Menu card.
        
        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            processing_server_location: Location of the processing server
        """
        if config is None:
            config = CardConfig(
                name="QlikMenu",
                position=CardPosition.BOTTOM_RIGHT,
                update_interval=21600,  # Update every 6 hours
                width=35,
                height=8,
                show_border=False,
                show_title=False,
            )
        super().__init__(config)
        self.processing_server_location = processing_server_location
        self._qlik_menu_widget: Optional[Static] = None
        self.logger = logging.getLogger("smart_mirror.plugins.qlik_menu")
        self.logger.info(f"QlikMenuCard initialized with server at {processing_server_location}")
    
    def compose(self) -> ComposeResult:
        """Compose the Qlik Menu display."""
        self._qlik_menu_widget = Static("Loading menu...")
        yield self._qlik_menu_widget
    
    async def _get_menu_text(self) -> str:
        """Get the current menu text formatted with colors."""
        try:
            menu_data = await self._get_menu()
            if not menu_data:
                return "[bold red] No menu data available[/bold red]"
            return self._format_menu(menu_data)
        except Exception as e:
            self.logger.error(f"Error fetching menu: {e}")
            return "[bold red] Failed to load menu[/bold red]"
    
    def _format_menu(self, menu_data: list) -> str:
        """Format menu data with day names and bullet points.
        
        Args:
            menu_data: List of dicts with 'day' and 'dishes' keys
            
        Returns:
            Formatted menu string with Rich markup
        """
        # Swedish day name to weekday number mapping (0=Monday, 6=Sunday)
        day_names = {
            "måndag": 0, "tisdag": 1, "onsdag": 2, "torsdag": 3,
            "fredag": 4, "lördag": 5, "söndag": 6
        }
        
        # Get current weekday (0=Monday, 6=Sunday)
        today = datetime.now().weekday()
        
        # If weekend, start from Monday (0)
        start_day = 0 if today >= 5 else today
        
        # Filter and sort menu items starting from start_day
        sorted_menu = []
        for item in menu_data:
            day_lower = item["day"].lower()
            if day_lower in day_names:
                day_num = day_names[day_lower]
                if day_num >= start_day:
                    sorted_menu.append((day_num, item))
        
        # Sort by day number and take first 2 days
        sorted_menu.sort(key=lambda x: x[0])
        sorted_menu = sorted_menu[:2]
        
        # Format output
        lines = []
        lines.append("[bold orange]🍽  Qlik Menu[/bold orange]")  # Header with icon
        lines.append("")
        
        for idx, (day_num, item) in enumerate(sorted_menu):
            # First day is orange, rest are gray
            color = "orange" if idx == 0 else "gray"
            lines.append(f"[bold {color}]{item['day']}:[/bold {color}]")
            
            # Add bullet points for dishes
            color_dish = "white" if idx == 0 else "gray"
            for dish in item["dishes"]:
                lines.append(f"[{color_dish}]  • {dish}[/{color_dish}]")
            
            # Add spacing between days (except after last day)
            if idx < len(sorted_menu) - 1:
                lines.append("")
        
        return "\n".join(lines)
    
    async def _get_menu(self) -> list:
        """Get the current menu from the server.
        
        Returns:
            List of dicts with 'day' and 'dishes' keys, or empty list on error
        """
        try:
            url = f"http://{self.processing_server_location}/actions/get-qlik-menu"
            self.logger.info(f"Fetching Qlik Menu from {url}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching menu: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching menu: {e}")
            return []

    async def update(self) -> None:
        """Update the menu text."""
        if self._qlik_menu_widget:
            self._qlik_menu_widget.update(await self._get_menu_text())

