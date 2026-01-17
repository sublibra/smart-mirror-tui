"""Tests for the smart mirror application."""

import pytest
from unittest.mock import patch

from smart_mirror.core.app import SmartMirrorApp
from smart_mirror.plugins.greeter import GreeterCard


@pytest.mark.asyncio
async def test_app_initialization():
    """Test that the app initializes correctly."""
    app = SmartMirrorApp()
    async with app.run_test() as pilot:
        assert pilot.app is not None
        assert pilot.app.width > 0
        assert pilot.app.height > 0
        assert len(pilot.app.cards) > 0


@pytest.mark.asyncio
async def test_cards_registered():
    """Test that default cards are registered."""
    app = SmartMirrorApp()
    async with app.run_test():
        assert "Clock" in app.cards
        assert "Weather" in app.cards
        assert "Greeter" in app.cards


@pytest.mark.asyncio
async def test_get_card():
    """Test getting a card by name."""
    app = SmartMirrorApp()
    async with app.run_test():
        clock = app.get_card("Clock")
        assert clock is not None
        assert clock.name == "Clock"


@pytest.mark.asyncio
async def test_get_nonexistent_card():
    """Test getting a card that doesn't exist."""
    app = SmartMirrorApp()
    async with app.run_test():
        card = app.get_card("NonExistent")
        assert card is None


@pytest.mark.asyncio
async def test_set_user_name():
    """Test setting user name for greeter."""
    app = SmartMirrorApp()
    async with app.run_test():
        app.set_user_name("Alice")
        greeter = app.get_card("Greeter")
        assert greeter is not None
        assert greeter._user_name == "Alice"


@pytest.mark.asyncio
async def test_card_compose():
    """Test that cards can compose widgets without errors."""
    app = SmartMirrorApp()
    async with app.run_test():
        for card in app.cards.values():
            widgets = list(card.compose())
            assert len(widgets) > 0


@pytest.mark.asyncio
async def test_card_update():
    """Test that cards can update without errors."""
    app = SmartMirrorApp()
    async with app.run_test():
        for card in app.cards.values():
            # Should not raise an exception
            await card.update()


@pytest.mark.asyncio
async def test_clock_compose():
    """Test clock card composition."""
    app = SmartMirrorApp()
    async with app.run_test():
        clock = app.get_card("Clock")
        widgets = list(clock.compose())
        assert len(widgets) > 0


@pytest.mark.asyncio
async def test_greeter_morning():
    """Test greeter shows morning greeting."""
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 8
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "morning" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_afternoon():
    """Test greeter shows afternoon greeting."""
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 14
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "afternoon" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_evening():
    """Test greeter shows evening greeting."""
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 18
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "evening" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_night():
    """Test greeter shows night greeting."""
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 22
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "night" in greeting.lower()
