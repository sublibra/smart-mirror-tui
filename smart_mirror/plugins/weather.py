"""Weather card for displaying current weather information."""

from typing import Optional

import httpx
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class WeatherCard(Card):
    """Weather card positioned at bottom left with icons and forecast."""

    DEFAULT_CSS = """
    #weather Static {
        text-align: left;
        padding: 1;
        align: center bottom;
    }

    #weather .weather-now {
        text-style: bold;
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
        self._error_message = "Loading..."
        self._weather_widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the weather display."""
        self._weather_widget = Static("Loading weather data...", classes="weather-now")
        yield self._weather_widget

    def _get_weather_icon(self, code: int) -> str:
        """Get weather icon for WMO weather code.

        Args:
            code: WMO weather code

        Returns:
            Weather icon emoji
        """
        return self.WEATHER_ICONS.get(code, "🌡️")

    def _format_weather(self) -> str:
        """Format weather data for display."""
        if self._error_message and self._error_message != "Loading...":
            return f"Error: {self._error_message}"

        if not self._weather_data:
            return "Loading weather data..."

        lines = []

        # Current weather
        current = self._weather_data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        code = current.get("weather_code", 0)
        wind = current.get("wind_speed_10m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")

        icon = self._get_weather_icon(code)
        lines.append(f"[bold]{icon}  Now: {temp}°C[/bold]")
        lines.append(f"💨 Wind: {wind} km/h")
        lines.append(f"💧 Humidity: {humidity}%")

        # 3-day forecast
        daily = self._weather_data.get("daily", {})
        if daily:
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            codes = daily.get("weather_code", [])
            times = daily.get("time", [])

            if len(temps_max) >= 3 and len(times) >= 3:
                lines.append("")
                for i in range(1, min(4, len(temps_max))):  # Next 3 days
                    try:
                        from datetime import datetime

                        day_name = datetime.fromisoformat(times[i]).strftime("%a")
                        icon = self._get_weather_icon(codes[i])
                        max_temp = temps_max[i]
                        min_temp = temps_min[i]
                        lines.append(f"  {day_name}: {icon} {max_temp}°/{min_temp}°C")
                    except (IndexError, ValueError):
                        continue

        return "\n".join(lines)

    async def update(self) -> None:
        """Fetch weather data from Open-Meteo API with forecast."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={self.latitude}&longitude={self.longitude}"
                    f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
                    f"&daily=temperature_2m_max,temperature_2m_min,weather_code"
                    f"&timezone=auto"
                )
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                self._weather_data = data
                self._error_message = ""
        except Exception as e:
            self._error_message = f"Error: {str(e)[:20]}"

        # Update widget
        if self._weather_widget:
            self._weather_widget.update(self._format_weather())
