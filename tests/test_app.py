"""Tests for the smart mirror application."""

import pytest
import asyncio
from smart_mirror.core.app import SmartMirrorApp


@pytest.fixture
def app():
    """Create a SmartMirrorApp instance for testing."""
    return SmartMirrorApp()


def test_app_initialization(app):
    """Test that the app initializes correctly."""
    assert app is not None
    assert app.width > 0
    assert app.height > 0
    assert len(app.cards) > 0


def test_cards_registered(app):
    """Test that default cards are registered."""
    assert "Clock" in app.cards
    assert "Weather" in app.cards
    assert "Greeter" in app.cards


def test_get_card(app):
    """Test getting a card by name."""
    clock = app.get_card("Clock")
    assert clock is not None
    assert clock.name == "Clock"


def test_get_nonexistent_card(app):
    """Test getting a card that doesn't exist."""
    card = app.get_card("NonExistent")
    assert card is None


def test_set_user_name(app):
    """Test setting user name for greeter."""
    app.set_user_name("Alice")
    greeter = app.get_card("Greeter")
    assert greeter is not None
    assert greeter._user_name == "Alice"


@pytest.mark.asyncio
async def test_card_compose():
    """Test that cards can compose widgets without errors."""
    app = SmartMirrorApp()
    
    for card in app.cards.values():
        widgets = list(card.compose())
        assert len(widgets) > 0


@pytest.mark.asyncio
async def test_card_update():
    """Test that cards can update without errors."""
    app = SmartMirrorApp()
    
    for card in app.cards.values():
        # Should not raise an exception
        await card.update()


@pytest.mark.asyncio
async def test_card_start_stop():
    """Test starting and stopping a card."""
    app = SmartMirrorApp()
    clock = app.get_card("Clock")
    
    assert not clock.is_running()
    await clock.start()
    assert clock.is_running()
    await clock.stop()
    assert not clock.is_running()


@pytest.mark.asyncio
async def test_clock_compose():
    """Test clock card composition."""
    app = SmartMirrorApp()
    clock = app.get_card("Clock")
    
    widgets = list(clock.compose())
    assert len(widgets) > 0


@pytest.mark.asyncio
async def test_greeter_morning():
    """Test greeter shows morning greeting."""
    from unittest.mock import patch
    from smart_mirror.plugins.greeter import GreeterCard
    
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 8
        
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "morning" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_afternoon():
    """Test greeter shows afternoon greeting."""
    from unittest.mock import patch
    from smart_mirror.plugins.greeter import GreeterCard
    
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 14
        
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "afternoon" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_evening():
    """Test greeter shows evening greeting."""
    from unittest.mock import patch
    from smart_mirror.plugins.greeter import GreeterCard
    
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 18
        
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "evening" in greeting.lower()


@pytest.mark.asyncio
async def test_greeter_night():
    """Test greeter shows night greeting."""
    from unittest.mock import patch
    from smart_mirror.plugins.greeter import GreeterCard
    
    with patch("smart_mirror.plugins.greeter.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 22
        
        greeter = GreeterCard(user_name="Bob")
        greeting = greeter._get_greeting()
        assert "night" in greeting.lower()
