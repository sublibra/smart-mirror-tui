"""Conftest for pytest fixtures and configuration."""

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def enable_default_cards(monkeypatch):
    """Ensure core cards are enabled during tests regardless of local .env."""

    monkeypatch.setenv("ENABLE_CLOCK", "true")
    monkeypatch.setenv("ENABLE_WEATHER", "true")
    monkeypatch.setenv("ENABLE_GREETER", "true")
    # Optional cards remain disabled unless tests set config explicitly
    monkeypatch.setenv("ENABLE_TRANSPORT", "")
    monkeypatch.setenv("ENABLE_CALENDAR", "")
    monkeypatch.setenv("TRANSPORT_API_KEY", "")
    monkeypatch.setenv("TRANSPORT_STATION_ID", "")
    monkeypatch.setenv("ENABLE_PIR", "")
