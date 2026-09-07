"""Tests for the weather card period forecast and dressing notes."""

from datetime import date, datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from smart_mirror.plugins.weather import (
    PeriodForecast,
    WeatherCard,
    dressing_notes,
    index_hourly,
    is_cold,
    is_rainy,
    is_windy,
)


def _slot(*, temp: float, code: int = 0, wind: float = 0.0, precip: float = 0.0) -> PeriodForecast:
    return PeriodForecast(
        temperature=temp,
        weather_code=code,
        wind_speed=wind,
        precipitation=precip,
    )


def _hourly_payload() -> dict:
    """Today 2026-09-07 and tomorrow 2026-09-08 at 08/12/18."""

    times = [
        "2026-09-07T08:00",
        "2026-09-07T12:00",
        "2026-09-07T18:00",
        "2026-09-08T08:00",
        "2026-09-08T12:00",
        "2026-09-08T18:00",
    ]
    return {
        "timezone": "Europe/Stockholm",
        "hourly": {
            "time": times,
            "temperature_2m": [8.4, 12.2, 9.1, 7.0, 10.6, 8.0],
            "weather_code": [1, 61, 3, 80, 2, 1],
            "wind_speed_10m": [12.0, 22.0, 18.0, 14.0, 10.0, 8.0],
            "precipitation": [0.0, 1.4, 0.0, 0.6, 0.0, 0.0],
        },
    }


def test_index_hourly_maps_date_and_hour():
    slots = index_hourly(_hourly_payload()["hourly"])
    morning = slots[(date(2026, 9, 7), 8)]
    noon = slots[(date(2026, 9, 7), 12)]
    tomorrow_morning = slots[(date(2026, 9, 8), 8)]

    assert morning.temperature == 8.4
    assert morning.weather_code == 1
    assert noon.weather_code == 61
    assert tomorrow_morning.precipitation == 0.6


def test_rain_wind_and_cold_helpers():
    assert is_rainy(_slot(temp=10, code=61))
    assert is_rainy(_slot(temp=10, code=1, precip=0.5))
    assert not is_rainy(_slot(temp=10, code=1, precip=0.0))
    assert is_windy(_slot(temp=10, wind=20.0))
    assert not is_windy(_slot(temp=10, wind=19.9))
    assert is_cold(_slot(temp=-0.1))
    assert not is_cold(_slot(temp=0.0))


def test_dressing_notes_umbrella_jacket_and_scarf():
    rainy_windy = _slot(temp=4, code=61, wind=25.0, precip=1.0)
    cold = _slot(temp=-2, code=1)

    notes = dressing_notes([rainy_windy, cold])
    assert notes == [
        "☔ Ta med paraply",
        "🧥 Det blåser och regnar",
        "🧣 Det är kallt",
    ]


def test_dressing_notes_umbrella_only():
    notes = dressing_notes([_slot(temp=8, code=61, wind=5.0)])
    assert notes == ["☔ Ta med paraply"]


def test_dressing_notes_scarf_only():
    notes = dressing_notes([_slot(temp=-3, code=0, wind=4.0)])
    assert notes == ["🧣 Det är kallt"]


def test_dressing_notes_empty_on_mild_clear_day():
    assert dressing_notes([_slot(temp=12, code=1, wind=8.0)]) == []


def test_format_weather_shows_today_and_tomorrow_periods():
    card = WeatherCard()
    card._weather_data = _hourly_payload()
    card._error_message = ""
    card._now_provider = lambda tz=None: datetime(
        2026, 9, 7, 7, 30, tzinfo=tz or ZoneInfo("Europe/Stockholm")
    )

    rendered = card._format_weather()

    assert "[bold]Idag[/bold]" in rendered
    assert "Morgon" in rendered
    assert "Lunch" in rendered
    assert "Kväll" in rendered
    assert "[bold]Imorgon[/bold]" in rendered
    assert "8°" in rendered
    assert "12°" in rendered
    assert "%" not in rendered
    assert "💨" in rendered
    assert "☔ Ta med paraply" in rendered
    assert "🧥 Det blåser och regnar" in rendered
    assert rendered.index("Idag") < rendered.index("Imorgon")
    assert rendered.count("Kväll") == 1


def test_format_weather_wind_icon_only_when_windy():
    card = WeatherCard()
    card._weather_data = _hourly_payload()
    card._error_message = ""
    card._now_provider = lambda tz=None: datetime(
        2026, 9, 7, 7, 30, tzinfo=tz or ZoneInfo("Europe/Stockholm")
    )

    rendered = card._format_weather()
    today_block, tomorrow_block = rendered.split("[bold]Imorgon[/bold]", 1)
    noon_line = next(line for line in today_block.splitlines() if line.startswith("Lunch"))
    morning_line = next(line for line in today_block.splitlines() if line.startswith("Morgon"))
    tomorrow_morning = next(
        line for line in tomorrow_block.splitlines() if line.startswith("Morgon")
    )

    assert "💨" in noon_line
    assert "💨" not in morning_line
    assert "💨" not in tomorrow_morning


def test_format_weather_dims_past_periods():
    card = WeatherCard()
    card._weather_data = _hourly_payload()
    card._error_message = ""
    card._now_provider = lambda tz=None: datetime(
        2026, 9, 7, 13, 0, tzinfo=tz or ZoneInfo("Europe/Stockholm")
    )

    rendered = card._format_weather()

    assert "[dim]Morgon" in rendered
    assert "[dim]Lunch" in rendered
    assert "[dim]Kväll" not in rendered


@pytest.mark.asyncio
async def test_weather_card_update_uses_hourly_forecast(monkeypatch):
    card = WeatherCard()
    list(card.compose())
    card._now_provider = lambda tz=None: datetime(
        2026, 9, 7, 7, 0, tzinfo=tz or ZoneInfo("Europe/Stockholm")
    )

    payload = _hourly_payload()
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: payload

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            assert "hourly=temperature_2m,weather_code,wind_speed_10m,precipitation" in url
            assert "forecast_days=2" in url
            return mock_response

    monkeypatch.setattr("smart_mirror.plugins.weather.httpx.AsyncClient", MockClient)

    await card.update()

    assert card._error_message == ""
    rendered = card._format_weather()
    assert "Idag" in rendered
    assert "Imorgon" in rendered
    assert "☔ Ta med paraply" in rendered
