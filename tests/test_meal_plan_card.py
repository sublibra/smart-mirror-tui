"""Tests for the meal plan card."""

from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest

from smart_mirror.plugins.base import CardPosition
from smart_mirror.plugins.meal_plan import (
    Meal,
    MealPlanCard,
    parse_meals,
    protein_icon,
    sort_meals,
)

MONDAY = datetime(2026, 9, 7, 8, 0)  # a Monday


def _card(**kwargs) -> MealPlanCard:
    defaults = {
        "feed_url": "https://example.supabase.co/functions/v1/meal-plan-feed?token=abc",
        "anon_key": "anon",
        "now_provider": lambda: MONDAY,
    }
    defaults.update(kwargs)
    return MealPlanCard(**defaults)


def test_protein_icons_match_shoplist():
    assert protein_icon("chicken") == "🐔"
    assert protein_icon("fish") == "🐟"
    assert protein_icon(None) == "🍽️"
    assert protein_icon("unknown") == "🍽️"


def test_parse_meals_skips_invalid_rows():
    meals = parse_meals(
        {
            "startedAt": "2026-09-01T00:00:00.000Z",
            "entries": [
                {"title": "Curry", "day": "mon", "protein": "chicken", "cooked": False},
                {"title": "  Fish stew  ", "day": "nope", "protein": "fish", "cooked": True},
                {"title": "", "day": "tue", "protein": "beef", "cooked": False},
                {"day": "wed"},
                "skip-me",
            ],
        }
    )
    assert meals == [
        Meal(title="Curry", day="mon", protein="chicken", cooked=False),
        Meal(title="Fish stew", day=None, protein="fish", cooked=True),
    ]


def test_parse_meals_empty_payload():
    assert parse_meals({}) == []
    assert parse_meals(None) == []
    assert parse_meals({"entries": []}) == []


def test_sort_meals_starts_from_today_and_omits_cooked():
    meals = [
        Meal(title="Sun", day="sun", protein=None, cooked=False),
        Meal(title="Tue cooked", day="tue", protein=None, cooked=True),
        Meal(title="Unscheduled", day=None, protein=None, cooked=False),
        Meal(title="Mon", day="mon", protein="chicken", cooked=False),
        Meal(title="Wed", day="wed", protein=None, cooked=False),
    ]
    ranked = sort_meals(meals, today_idx=0)
    assert [m.title for m in ranked] == [
        "Mon",
        "Wed",
        "Sun",
        "Unscheduled",
    ]


def test_format_puts_swedish_day_on_the_title_line():
    card = _card()
    card._error_message = ""
    card._meals = [
        Meal(title="Curry", day="mon", protein="chicken", cooked=False),
        Meal(title="Stew", day="tue", protein="fish", cooked=False),
        Meal(title="Leftovers", day="mon", protein="chicken", cooked=True),
        Meal(title="Soup", day=None, protein=None, cooked=False),
    ]
    formatted = card._format_plan()
    assert "🍽  This week" in formatted
    assert "🐔 Curry (mån)" in formatted
    assert "🐟 Stew (tis)" in formatted
    assert "Leftovers" not in formatted
    assert "Soup" in formatted
    assert "Soup (" not in formatted
    assert "strike" not in formatted


def test_format_empty_and_error():
    card = _card()
    card._error_message = ""
    card._meals = []
    assert "No meals this week" in card._format_plan()

    card._error_message = "HTTP Error: 404"
    assert "Meal Plan Error" in card._format_plan()


def test_format_hides_week_when_everything_is_cooked():
    card = _card()
    card._error_message = ""
    card._meals = [
        Meal(title="Leftovers", day="mon", protein="chicken", cooked=True),
    ]
    assert "No meals this week" in card._format_plan()
    assert "Leftovers" not in card._format_plan()


def test_max_items_limits_display():
    card = _card(max_items=2)
    card._error_message = ""
    card._meals = [
        Meal(title="One", day="mon", protein=None, cooked=False),
        Meal(title="Two", day="tue", protein=None, cooked=False),
        Meal(title="Three", day="wed", protein=None, cooked=False),
    ]
    formatted = card._format_plan()
    assert "One" in formatted
    assert "Two" in formatted
    assert "Three" not in formatted


def test_default_position():
    assert _card().config.position == CardPosition.TOP_RIGHT
    assert _card().config.update_interval == 300
    assert _card(update_interval=120).config.update_interval == 120
    assert _card(update_interval=1).config.update_interval == 5


@pytest.mark.asyncio
async def test_compose_and_missing_url():
    card = MealPlanCard(feed_url="")
    widgets = list(card.compose())
    assert len(widgets) == 1
    await card.update()
    assert "No feed URL configured" in card._error_message


@pytest.mark.asyncio
async def test_update_fetches_and_renders(monkeypatch):
    payload = {
        "startedAt": "2026-09-07T00:00:00.000Z",
        "entries": [
            {"title": "Curry", "day": "mon", "protein": "chicken", "cooked": False},
        ],
    }
    card = _card()
    list(card.compose())
    monkeypatch.setattr(card, "_fetch_payload", AsyncMock(return_value=payload))
    await card.update()
    assert card._error_message == ""
    assert card._meals[0].title == "Curry"
    assert "Curry" in card._format_plan()


def test_app_registers_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_MEAL_PLAN", "true")
    monkeypatch.setenv(
        "MEAL_PLAN_FEED_URL",
        "https://example.supabase.co/functions/v1/meal-plan-feed?token=abc",
    )
    monkeypatch.setenv("MEAL_PLAN_ANON_KEY", "anon")
    monkeypatch.setenv("MEAL_PLAN_UPDATE_INTERVAL", "120")
    from smart_mirror.core.app import SmartMirrorApp

    app = SmartMirrorApp()
    card = app.get_card("MealPlan")
    assert card is not None
    assert card.feed_url.endswith("token=abc")
    assert card.config.update_interval == 120


@pytest.mark.asyncio
async def test_update_http_error(monkeypatch):
    card = _card()
    list(card.compose())
    monkeypatch.setattr(
        card,
        "_fetch_payload",
        AsyncMock(side_effect=httpx.HTTPError("boom")),
    )
    await card.update()
    assert "HTTP Error" in card._error_message
