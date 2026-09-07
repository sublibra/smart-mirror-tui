"""Weather card for morning, noon, and evening dressing notes."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional
from zoneinfo import ZoneInfo

import httpx
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition

MORNING_HOUR = 8
NOON_HOUR = 12
EVENING_HOUR = 18
TODAY_PERIODS = (
    ("Morgon", MORNING_HOUR),
    ("Lunch", NOON_HOUR),
    ("Kväll", EVENING_HOUR),
)
TOMORROW_PERIODS = (
    ("Morgon", MORNING_HOUR),
    ("Lunch", NOON_HOUR),
)

WINDY_KMH = 20.0
COLD_C = 0.0
RAIN_MM = 0.2
RAIN_CODES = frozenset(
    {
        51,
        53,
        55,
        56,
        57,
        61,
        63,
        65,
        66,
        67,
        80,
        81,
        82,
        95,
        96,
        99,
    }
)


@dataclass(frozen=True)
class PeriodForecast:
    """Weather at a single hour of the day."""

    temperature: float
    weather_code: int
    wind_speed: float
    precipitation: float


def _optional_float(values: list, index: int, default: float = 0.0) -> float:
    """Read a numeric hourly value, treating missing entries as default."""

    if index >= len(values) or values[index] is None:
        return default
    try:
        return float(values[index])
    except (TypeError, ValueError):
        return default


def index_hourly(hourly: dict) -> dict[tuple, PeriodForecast]:
    """Map (date, hour) to forecast values from an Open-Meteo hourly block."""

    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    codes = hourly.get("weather_code") or []
    winds = hourly.get("wind_speed_10m") or []
    precips = hourly.get("precipitation") or []

    slots: dict[tuple, PeriodForecast] = {}
    for i, stamp in enumerate(times):
        if not isinstance(stamp, str) or i >= len(temps) or i >= len(codes):
            continue
        try:
            dt = datetime.fromisoformat(stamp)
            temperature = float(temps[i])
            weather_code = int(codes[i])
        except (TypeError, ValueError):
            continue

        slots[(dt.date(), dt.hour)] = PeriodForecast(
            temperature=temperature,
            weather_code=weather_code,
            wind_speed=_optional_float(winds, i),
            precipitation=_optional_float(precips, i),
        )
    return slots


def is_rainy(slot: PeriodForecast) -> bool:
    """True when the period is raining, drizzling, or stormy."""

    return slot.weather_code in RAIN_CODES or slot.precipitation >= RAIN_MM


def is_windy(slot: PeriodForecast) -> bool:
    """True when wind is strong enough to feel it outdoors."""

    return slot.wind_speed >= WINDY_KMH


def is_cold(slot: PeriodForecast) -> bool:
    """True when temperature is below freezing."""

    return slot.temperature < COLD_C


def dressing_notes(today_slots: list[PeriodForecast]) -> list[str]:
    """Short dressing hints from today's morning, noon, and evening."""

    if not today_slots:
        return []

    rainy = any(is_rainy(slot) for slot in today_slots)
    windy = any(is_windy(slot) for slot in today_slots)
    cold = any(is_cold(slot) for slot in today_slots)

    notes: list[str] = []
    if rainy:
        notes.append("☔ Ta med paraply")
    if rainy and windy:
        notes.append("🧥 Det blåser och regnar")
    if cold:
        notes.append("🧣 Det är kallt")
    return notes


class WeatherCard(Card):
    """Weather card positioned at middle left with period forecast."""

    DEFAULT_CSS = """
    #weather Static {
        text-align: left;
        padding: 0 1;
        align: left top;
    }

    #weather .weather-now {
        color: white;
    }
    """

    # Weather condition code to icon mapping (WMO Weather codes)
    WEATHER_ICONS = {
        0: "☀️",  # Clear sky
        1: "🌤️",  # Mainly clear
        2: "⛅",  # Partly cloudy
        3: "☁️",  # Overcast
        45: "🌫️",  # Foggy
        48: "🌫️",  # Depositing rime fog
        51: "🌦️",  # Drizzle light
        53: "🌦️",  # Drizzle moderate
        55: "🌧️",  # Drizzle dense
        61: "🌧️",  # Rain slight
        63: "🌧️",  # Rain moderate
        65: "🌧️",  # Rain heavy
        71: "🌨️",  # Snow slight
        73: "🌨️",  # Snow moderate
        75: "🌨️",  # Snow heavy
        77: "❄️",  # Snow grains
        80: "🌦️",  # Rain showers slight
        81: "🌧️",  # Rain showers moderate
        82: "⛈️",  # Rain showers violent
        85: "🌨️",  # Snow showers slight
        86: "🌨️",  # Snow showers heavy
        95: "⛈️",  # Thunderstorm
        96: "⛈️",  # Thunderstorm with slight hail
        99: "⛈️",  # Thunderstorm with heavy hail
    }

    def __init__(
        self,
        config: Optional[CardConfig] = None,
        latitude: float = 52.5200,
        longitude: float = 13.4050,
    ):
        """Initialize the weather card.

        Args:
            config: Optional CardConfig. If not provided, uses defaults.
            latitude: Location latitude for weather data
            longitude: Location longitude for weather data
        """
        if config is None:
            config = CardConfig(
                name="Weather",
                title="Väder",
                position=CardPosition.MIDDLE_LEFT,
                update_interval=300,  # Update every 5 minutes
                width=40,
                height=12,
                border_style="blue",
                text_align="left",
            )
        super().__init__(config)
        self.latitude = latitude
        self.longitude = longitude
        self._weather_data: dict = {}
        self._error_message = "Laddar..."
        self._weather_widget: Optional[Static] = None
        self._now_provider: Callable[..., datetime] = datetime.now

    def compose(self) -> ComposeResult:
        """Compose the weather display."""
        self._weather_widget = Static("Hämtar väder...", classes="weather-now")
        yield self._weather_widget

    def _get_weather_icon(self, code: int) -> str:
        """Get weather icon for WMO weather code.

        Args:
            code: WMO weather code

        Returns:
            Weather icon emoji
        """
        return self.WEATHER_ICONS.get(code, "🌡️")

    def _format_period_line(self, label: str, slot: Optional[PeriodForecast]) -> str:
        """Format one morning/noon/evening row."""

        if slot is None:
            return f"{label:<9}—"

        icon = self._get_weather_icon(slot.weather_code)
        temp = int(round(slot.temperature))
        wind = " 💨" if is_windy(slot) else ""
        return f"{label:<9}{icon}  {temp:>3}°{wind}"

    def _local_now(self) -> datetime:
        """Current time in the forecast's local timezone when available."""

        tz_name = self._weather_data.get("timezone")
        if isinstance(tz_name, str) and tz_name:
            try:
                return self._now_provider(ZoneInfo(tz_name))
            except Exception:
                pass
        now = self._now_provider()
        return now

    def _format_weather(self) -> str:
        """Format weather data for display."""
        if self._error_message and self._error_message != "Laddar...":
            return f"Fel: {self._error_message}"

        if not self._weather_data:
            return "Hämtar väder..."

        hourly = self._weather_data.get("hourly") or {}
        slots = index_hourly(hourly)
        now = self._local_now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        lines: list[str] = ["[bold]Idag[/bold]"]
        today_forecasts: list[PeriodForecast] = []
        for label, hour in TODAY_PERIODS:
            slot = slots.get((today, hour))
            line = self._format_period_line(label, slot)
            if slot is not None and now.hour > hour:
                line = f"[dim]{line}[/dim]"
            lines.append(line)
            if slot is not None:
                today_forecasts.append(slot)

        lines.append("")
        lines.append("[bold]Imorgon[/bold]")
        for label, hour in TOMORROW_PERIODS:
            slot = slots.get((tomorrow, hour))
            lines.append(self._format_period_line(label, slot))

        notes = dressing_notes(today_forecasts)
        if notes:
            lines.append("")
            lines.extend(notes)

        return "\n".join(lines)

    async def update(self) -> None:
        """Fetch hourly weather from Open-Meteo for today and tomorrow."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={self.latitude}&longitude={self.longitude}"
                    f"&hourly=temperature_2m,weather_code,wind_speed_10m,precipitation"
                    f"&forecast_days=2"
                    f"&timezone=auto"
                )
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                self._weather_data = data
                self._error_message = ""
        except Exception as e:
            self._error_message = f"Fel: {str(e)[:20]}"

        if self._weather_widget:
            self._weather_widget.update(self._format_weather())
