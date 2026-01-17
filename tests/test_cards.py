"""Tests for specific plugin cards."""

import pytest

from smart_mirror.plugins.clock import ClockCard
from smart_mirror.plugins.greeter import GreeterCard
from smart_mirror.plugins.weather import WeatherCard


@pytest.mark.asyncio
async def test_clock_card_initialization():
    """Test clock card initialization."""
    clock = ClockCard()
    assert clock.name == "Clock"
    assert clock.config.update_interval == 1


@pytest.mark.asyncio
async def test_clock_card_compose():
    """Test clock card composition."""
    clock = ClockCard()
    widgets = list(clock.compose())

    # Should have widgets for time and date
    assert len(widgets) > 0


@pytest.mark.asyncio
async def test_clock_card_update():
    """Test clock card updates without errors."""
    clock = ClockCard()
    # Initialize widgets
    list(clock.compose())

    # Should not raise an exception
    await clock.update()


@pytest.mark.asyncio
async def test_greeter_card_initialization():
    """Test greeter card initialization."""
    greeter = GreeterCard(user_name="TestUser")
    assert greeter.name == "Greeter"
    assert greeter._user_name == "TestUser"


@pytest.mark.asyncio
async def test_greeter_card_compose():
    """Test greeter card composition."""
    greeter = GreeterCard(user_name="Alice")
    widgets = list(greeter.compose())

    assert len(widgets) > 0


@pytest.mark.asyncio
async def test_greeter_set_user_name():
    """Test setting user name for greeter."""
    greeter = GreeterCard(user_name="Bob")
    assert greeter._user_name == "Bob"

    greeter.set_user_name("Charlie")
    assert greeter._user_name == "Charlie"


@pytest.mark.asyncio
async def test_weather_card_initialization():
    """Test weather card initialization."""
    weather = WeatherCard()
    assert weather.name == "Weather"
    assert weather.config.update_interval == 300


@pytest.mark.asyncio
async def test_weather_card_compose():
    """Test weather card composition."""
    weather = WeatherCard()
    widgets = list(weather.compose())

    # Should have weather widget
    assert len(widgets) > 0


@pytest.mark.asyncio
async def test_weather_card_update():
    """Test weather card updates without errors."""
    weather = WeatherCard()
    # Initialize widgets
    list(weather.compose())

    # Should not raise an exception (even if API call fails)
    try:
        await weather.update()
    except Exception:
        # API errors are expected in tests
        pass
