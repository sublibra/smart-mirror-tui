"""Meal plan card for this week's dinners from the Shoplist feed."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import httpx
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_LABELS = {
    "mon": "mån",
    "tue": "tis",
    "wed": "ons",
    "thu": "tor",
    "fri": "fre",
    "sat": "lör",
    "sun": "sön",
}

# Same emoji set as Shoplist's protein tags.
PROTEIN_ICONS = {
    "chicken": "🐔",
    "beef": "🥩",
    "pork": "🐷",
    "lamb": "🐑",
    "fish": "🐟",
    "vegetarian": "🧀",
    "vegan": "🌱",
    "egg": "🥚",
    "other": "🍽️",
}


@dataclass(frozen=True)
class Meal:
    """One dinner from the active week."""

    title: str
    day: Optional[str]
    protein: Optional[str]
    cooked: bool


def protein_icon(protein: Optional[str]) -> str:
    """Return the emoji for a protein tag."""
    if protein is None:
        return PROTEIN_ICONS["other"]
    return PROTEIN_ICONS.get(protein, PROTEIN_ICONS["other"])


def parse_meals(payload: object) -> list[Meal]:
    """Extract meals from a feed JSON payload."""
    if not isinstance(payload, dict):
        return []
    raw = payload.get("entries")
    if not isinstance(raw, list):
        return []

    meals: list[Meal] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        day = item.get("day")
        if day not in DAYS:
            day = None
        protein = item.get("protein")
        if not isinstance(protein, str) or protein not in PROTEIN_ICONS:
            protein = None
        meals.append(
            Meal(
                title=title.strip(),
                day=day,
                protein=protein,
                cooked=item.get("cooked") is True,
            )
        )
    return meals


def day_sort_key(day: Optional[str], today_idx: int) -> int:
    """Sort key: today first, then the rest of the week, unscheduled last."""
    if day is None or day not in DAYS:
        return 7
    return (DAYS.index(day) - today_idx) % 7


def sort_meals(meals: list[Meal], today_idx: int) -> list[Meal]:
    """Uncooked meals by day from today, then original order. Cooked are omitted."""
    uncooked = [(i, meal) for i, meal in enumerate(meals) if not meal.cooked]
    ranked = sorted(
        uncooked,
        key=lambda pair: (day_sort_key(pair[1].day, today_idx), pair[0]),
    )
    return [meal for _, meal in ranked]


class MealPlanCard(Card):
    """Meal plan card displaying this week's dinners from Shoplist."""

    DEFAULT_CSS = """
    #mealplan Static {
        text-align: left;
        padding: 1;
    }

    #mealplan .meal-plan-title {
        text-style: bold;
        color: white;
    }
    """

    def __init__(
        self,
        config: Optional[CardConfig] = None,
        feed_url: str = "",
        anon_key: str = "",
        max_items: int = 6,
        update_interval: int = 300,
        now_provider: Optional[Callable[[], datetime]] = None,
    ):
        """Initialize the meal plan card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            feed_url: Shoplist meal-plan-feed URL including the secret token.
            anon_key: Public Supabase anon key (required by the function gateway).
            max_items: Maximum number of dinners to display.
            update_interval: Seconds between feed refreshes (minimum 5).
            now_provider: Optional clock for tests.
        """
        if config is None:
            config = CardConfig(
                name="MealPlan",
                title="Meny",
                show_title=False,
                position=CardPosition.BOTTOM_LEFT,
                update_interval=max(5, update_interval),
                width=40,
                height=12,
                border_style="yellow",
                text_align="left",
            )
        super().__init__(config)
        self.feed_url = feed_url
        self.anon_key = anon_key
        self.max_items = max_items
        self._now_provider = now_provider or datetime.now
        self._meals: list[Meal] = []
        self._error_message = "Laddar..."
        self._widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the meal plan display."""
        self._widget = Static("Hämtar meny...", classes="meal-plan-title")
        yield self._widget

    def _meal_label(self, meal: Meal) -> str:
        """Title with optional Swedish short day, e.g. 'Curry (mån)'."""
        if meal.day is None:
            return meal.title
        day_label = DAY_LABELS.get(meal.day)
        if not day_label:
            return meal.title
        return f"{meal.title} ({day_label})"

    def _format_plan(self) -> str:
        """Format meals for display."""
        if self._error_message and self._error_message != "Laddar...":
            return f"[bold red]Menyfel[/bold red]\n{self._error_message}"

        if not self._meals:
            return "[bold]🏠  Meny[/bold]\n\nIngen meny denna vecka"

        today_idx = self._now_provider().weekday()
        ranked = sort_meals(self._meals, today_idx)[: self.max_items]
        if not ranked:
            return "[bold]🏠  Meny[/bold]\n\nIngen meny denna vecka"

        lines = ["[bold]🏠  Meny[/bold]", ""]
        for i, meal in enumerate(ranked):
            icon = protein_icon(meal.protein)
            label = self._meal_label(meal)
            if i == 0:
                lines.append(f"[bold]{icon} {label}[/bold]")
            else:
                lines.append(f"[dim]{icon} {label}[/dim]")

            if i < len(ranked) - 1:
                lines.append("")

        return "\n".join(lines)

    async def _fetch_payload(self) -> object:
        """GET the Shoplist feed JSON."""
        headers = {}
        if self.anon_key:
            headers["apikey"] = self.anon_key
            headers["Authorization"] = f"Bearer {self.anon_key}"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(self.feed_url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def update(self) -> None:
        """Fetch meal plan data from the Shoplist feed."""
        if not self.feed_url:
            self._error_message = "Ingen URL konfigurerad"
            if self._widget:
                self._widget.update(self._format_plan())
            return

        try:
            payload = await self._fetch_payload()
            self._meals = parse_meals(payload)
            self._error_message = ""
        except httpx.HTTPError as e:
            self._error_message = f"HTTP-fel: {str(e)[:30]}"
            self.log(f"HTTP error fetching meal plan: {e}", level="error")
        except Exception as e:
            self._error_message = f"Fel: {str(e)[:30]}"
            self.log(f"Error fetching meal plan: {e}", level="error")

        if self._widget:
            self._widget.update(self._format_plan())
