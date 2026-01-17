"""Public menu card using web scraping from Qlik restaurant."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class QlikMenuCard(Card):
    """Get the Qlik Menu for the coming week"""

    DEFAULT_CSS = """
    #qlik_menu Static {
        text-style: bold;
        color: orange;
        text-align: center;
        content-align: center middle;
    }
    """

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

    # Text labels to icons mapping (case-insensitive)
    LABEL_ICONS = {
        "green": "🥬",
        "local": "🌲",
        "world wide": "🌍",
    }

    # Web scraping selectors
    DISH_TITLE_SELECTOR = "h3.elementor-heading-title.elementor-size-default"
    DISH_LIST_SELECTOR = "ul.elementor-price-list"
    DISH_NAME_SELECTOR = "span.elementor-price-list-title"
    DISH_DESC_SELECTOR = "p.elementor-price-list-description"
    MENU_URL = "https://smartakok.se/vara-kok/qlik/"

    def __init__(
        self,
        config: Optional[CardConfig] = None,
        *,
        processing_server_location: str = "",
    ) -> None:
        """Initialize the Qlik Menu card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            processing_server_location: Unused, kept for compatibility.
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
        self._qlik_menu_widget: Optional[Static] = None
        self.log("QlikMenuCard initialized")

    def compose(self) -> ComposeResult:
        """Compose the Qlik Menu display."""
        self._qlik_menu_widget = Static("Loading menu...")
        yield self._qlik_menu_widget

    async def _get_menu_text(self) -> str:
        """Get the current menu text formatted with colors."""
        try:
            menu_data = await self._fetch_menu()
            if not menu_data:
                return "[bold red]No menu data available[/bold red]"
            return self._format_menu(menu_data)
        except Exception as exc:  # pragma: no cover
            self.log(f"Error fetching menu: {exc}")
            return "[bold red]Failed to load menu[/bold red]"

    def _format_menu(self, menu_data: List[Dict[str, Any]]) -> str:
        """Format menu data with day names and bullet points.

        Args:
            menu_data: List of dicts with 'day' and 'dishes' keys

        Returns:
            Formatted menu string with Rich markup
        """
        today = datetime.now().weekday()
        start_day = 0 if today >= 5 else today

        # Filter and sort menu items starting from today
        sorted_menu = []
        for item in menu_data:
            day_lower = item["day"].lower()
            if day_lower in self.DAY_NAMES:
                day_num = self.DAY_NAMES[day_lower]
                if day_num >= start_day:
                    sorted_menu.append((day_num, item))

        sorted_menu.sort(key=lambda x: x[0])
        sorted_menu = sorted_menu[:2]

        # Build output lines
        lines = ["[bold orange]🍽  Qlik Menu[/bold orange]", ""]

        for idx, (_day_num, item) in enumerate(sorted_menu):
            color = "orange" if idx == 0 else "gray"
            lines.append(f"[bold {color}]{item['day']}:[/bold {color}]")

            color_dish = "white" if idx == 0 else "gray"
            for dish in item["dishes"]:
                lines.append(f"[{color_dish}]  • {dish}[/{color_dish}]")

            if idx < len(sorted_menu) - 1:
                lines.append("")

        return "\n".join(lines)

    def _replace_labels_with_icons(self, text: str) -> str:
        """Replace text labels with icons (case-insensitive).

        Args:
            text: Text that may contain label names

        Returns:
            Text with labels replaced by icons
        """
        result = text
        text_lower = text.lower()
        for label, icon in self.LABEL_ICONS.items():
            idx = 0
            while True:
                idx = text_lower.find(label, idx)
                if idx == -1:
                    break
                result = result[:idx] + icon + result[idx + len(label) :]
                text_lower = text_lower[:idx] + icon + text_lower[idx + len(label) :]
                idx += len(icon)
        return result

    async def _fetch_menu(self) -> List[Dict[str, Any]]:
        """Fetch the current menu from the restaurant website.

        Returns:
            List of dicts with 'day' and 'dishes' keys, or empty list on error
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.MENU_URL)
                response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return self._parse_menu_html(soup)
        except httpx.HTTPError as exc:
            self.log(f"HTTP error: {exc}")
            return []
        except Exception as exc:  # pragma: no cover
            self.log(f"Unexpected error: {exc}")
            return []

    def _parse_menu_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse menu HTML into structured data.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of dicts with 'day' and 'dishes' keys
        """
        menu: List[Dict[str, Any]] = []
        title = soup.select_one(self.DISH_TITLE_SELECTOR)

        while title is not None:
            day_text = title.text.strip()
            if day_text.lower() in self.DAY_NAMES:
                dishes = self._extract_dishes(title)
                menu.append({"day": day_text, "dishes": dishes})
            title = title.find_next("h3", class_="elementor-heading-title elementor-size-default")

        return menu

    def _extract_dishes(self, title_element: Any) -> List[str]:
        """Extract dishes for a given day from HTML.

        Args:
            title_element: BeautifulSoup element containing the day title

        Returns:
            List of formatted dish strings
        """
        dishes: List[str] = []
        dish_list = title_element.find_next("ul", class_="elementor-price-list")
        if not dish_list:
            return dishes

        for dish_span in dish_list.find_all("span", class_="elementor-price-list-title"):
            dish_name = dish_span.text.strip()
            desc_elem = dish_span.find_next("p", class_="elementor-price-list-description")
            dish_desc = desc_elem.text.strip() if desc_elem else ""

            # Format: "Dish Name: Description" with icon replacements
            dish_text = f"{dish_name}: {dish_desc}" if dish_desc else dish_name
            dish_text = self._replace_labels_with_icons(dish_text)
            dishes.append(dish_text)

        return dishes

    async def update(self) -> None:
        """Update the menu display."""
        if self._qlik_menu_widget:
            text = await self._get_menu_text()
            self._qlik_menu_widget.update(text)
