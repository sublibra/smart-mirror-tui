"""Tests for the transport departures card."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from smart_mirror.plugins.transport import TransportCard


@pytest.mark.asyncio
async def test_transport_card_initialization():
    card = TransportCard(api_key="key", station_id="123")
    assert card.name == "Transport"
    assert card.station_id == "123"
    assert card.config.update_interval == 60


@pytest.mark.asyncio
async def test_transport_card_compose():
    card = TransportCard(api_key="key", station_id="123")
    widgets = list(card.compose())
    assert len(widgets) == 1


@pytest.mark.asyncio
async def test_transport_card_update_with_delay(monkeypatch):
    now = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    expected_time = "2024-01-01T10:08:00"
    timetable_time = "2024-01-01T10:05:00"

    payload = {
        "departures": [
            {
                "scheduled": timetable_time,
                "realtime": expected_time,
                "delay": 180,  # 3 minutes delay in seconds
                "canceled": False,
                "route": {
                    "designation": "50",
                    "direction": "Central",
                    "transport_mode": "BUS",
                },
            }
        ]
    }

    card = TransportCard(api_key="key", station_id="123", delay_threshold=60)
    list(card.compose())
    card._now_provider = lambda tz=None: now  # type: ignore[assignment]
    monkeypatch.setattr(card, "_fetch_departures", AsyncMock(return_value=payload))

    await card.update()
    renderable_str = str(card._last_render)

    assert "Central" in renderable_str
    assert "in 8m" in renderable_str
    assert "⚠️  +3m" in renderable_str


@pytest.mark.asyncio
async def test_transport_card_update_without_delay(monkeypatch):
    now = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    expected_time = "2024-01-01T10:06:00"
    timetable_time = "2024-01-01T10:05:00"

    payload = {
        "departures": [
            {
                "scheduled": timetable_time,
                "realtime": expected_time,
                "delay": 60,  # 1 minute delay, below 180s threshold
                "canceled": False,
                "route": {
                    "designation": "A",
                    "direction": "North",
                    "transport_mode": "TRAIN",
                },
            }
        ]
    }

    card = TransportCard(api_key="key", station_id="123", delay_threshold=180)
    list(card.compose())
    card._now_provider = lambda tz=None: now  # type: ignore[assignment]
    monkeypatch.setattr(card, "_fetch_departures", AsyncMock(return_value=payload))

    await card.update()

    assert "[WARN" not in card._last_render


@pytest.mark.asyncio
async def test_transport_card_missing_configuration():
    card = TransportCard()
    list(card.compose())

    await card.update()

    assert "not configured" in card._last_render.lower()


@pytest.mark.asyncio
async def test_transport_card_no_departures(monkeypatch):
    payload = {"departures": []}
    card = TransportCard(api_key="key", station_id="123")
    list(card.compose())
    monkeypatch.setattr(card, "_fetch_departures", AsyncMock(return_value=payload))

    await card.update()

    assert "no upcoming" in card._last_render.lower()
