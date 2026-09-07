"""Getting Qlik Menu for the coming week."""

from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition

QLIK_MENU_URL = "https://smartakok.se/vara-kok/qlik/"
_HEADING_CLASS = "elementor-heading-title elementor-size-default"

# Swedish day name to weekday number mapping (0=Monday, 6=Sunday)
DAY_NAMES = {
    "måndag": 0,
    "tisdag": 1,
    "onsdag": 2,
    "torsdag": 3,
    "fredag": 4,
    "lördag": 5,
    "söndag": 6,
}


def parse_qlik_menu(html: str) -> list[dict]:
    """Parse Smarta Kök's Qlik lunch page into day/dish entries.

    Args:
        html: Raw HTML from the Qlik menu page.

    Returns:
        List of dicts with ``day`` and ``dishes`` keys. Non-day headings
        such as opening hours are skipped.
    """
    soup = BeautifulSoup(html, "html.parser")
    menu: list[dict] = []
    title = soup.find("h3", class_=_HEADING_CLASS)

    while title is not None:
        day = title.get_text(strip=True)
        if day.lower() in DAY_NAMES:
            dishes = []
            ul = title.find_next("ul", class_="elementor-price-list")
            if ul:
                for dish in ul.find_all("span", class_="elementor-price-list-title"):
                    description = dish.find_next("p", class_="elementor-price-list-description")
                    dish_title = dish.get_text(strip=True)
                    dish_desc = description.get_text(strip=True) if description else ""
                    if dish_title and dish_desc:
                        dishes.append(f"{dish_title}: {dish_desc}")
                    elif dish_title or dish_desc:
                        dishes.append(dish_title or dish_desc)
            menu.append({"day": day, "dishes": dishes})
        title = title.find_next("h3", class_=_HEADING_CLASS)

    return menu


class QlikMenuCard(Card):
    """Get the Qlik Menu for the coming week"""

    DEFAULT_CSS = """
    #qlik_menu Static {
        text-style: bold;
        color: orange;
        text-align: center;
        align: center bottom;
    }
    """

    DAY_NAMES = DAY_NAMES

    def __init__(self, config: Optional[CardConfig] = None):
        """Initialize the Menu card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
        """
        if config is None:
            config = CardConfig(
                name="QlikMenu",
                position=CardPosition.BOTTOM_RIGHT,
                update_interval=7200,  # Update every 2 hours
                width=35,
                height=8,
                show_border=False,
                show_title=False,
            )
        super().__init__(config)
        self._qlik_menu_widget: Optional[Static] = None
        self.log("QlikMenuCard initialized")

    def compose(self) -> ComposeResult:
        """Compose the Qlik Menu display."""
        self._qlik_menu_widget = Static("Hämtar meny...")
        yield self._qlik_menu_widget

    async def _get_menu_text(self) -> str:
        """Get the current menu text formatted with colors."""
        try:
            menu_data = await self._get_menu()
            if not menu_data:
                return "[bold red] Ingen meny tillgänglig[/bold red]"
            return self._format_menu(menu_data)
        except Exception as e:
            self.log(f"Error fetching menu: {e}", level="error")
            return "[bold red] Kunde inte hämta meny[/bold red]"

    def _format_menu(self, menu_data: list) -> str:
        """Format menu data with day names and bullet points.

        Args:
            menu_data: List of dicts with 'day' and 'dishes' keys

        Returns:
            Formatted menu string with Rich markup
        """
        # Get current weekday (0=Monday, 6=Sunday)
        today = datetime.now().weekday()
        hour = datetime.now().hour

        # If weekend, start from Monday (0)
        if today >= 5:
            start_day = 0
        else:
            start_day = today
            # If after 09:00, shift to next day
            if hour >= 9:
                start_day += 1

        # Filter and sort menu items starting from start_day
        sorted_menu = []
        for item in menu_data:
            day_lower = item["day"].lower()
            if day_lower in self.DAY_NAMES:
                day_num = self.DAY_NAMES[day_lower]
                if day_num >= start_day:
                    sorted_menu.append((day_num, item))

        # Sort by day number and take first 2 days
        sorted_menu.sort(key=lambda x: x[0])
        sorted_menu = sorted_menu[:2]

        # Format output
        lines = []
        lines.append("[bold orange]🏢  Meny[/bold orange]")
        lines.append("")

        for idx, (_day_num, item) in enumerate(sorted_menu):
            # First day is orange, rest are gray
            color = "orange" if idx == 0 else "gray"
            lines.append(f"[bold {color}]{item['day']}:[/bold {color}]")

            # Add bullet points for dishes
            color_dish = "white" if idx == 0 else "dim"
            for dish in item["dishes"]:
                lines.append(f"[{color_dish}]- {dish}[/{color_dish}]")

            # Add spacing between days (except after last day)
            if idx < len(sorted_menu) - 1:
                lines.append("")

        return "\n".join(lines)

    async def _get_menu(self) -> list:
        """Fetch and parse the Qlik lunch menu from Smarta Kök.

        Returns:
            List of dicts with 'day' and 'dishes' keys, or empty list on error
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(QLIK_MENU_URL)
                response.raise_for_status()
                return parse_qlik_menu(response.text)
        except httpx.HTTPError as e:
            self.log(f"HTTP error fetching menu: {e}", level="error")
            return []
        except Exception as e:
            self.log(f"Unexpected error fetching menu: {e}", level="error")
            return []

    async def update(self) -> None:
        """Update the menu text."""
        if self._qlik_menu_widget:
            self._qlik_menu_widget.update(await self._get_menu_text())
