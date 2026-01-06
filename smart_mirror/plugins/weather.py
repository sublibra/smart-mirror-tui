"""Weather card for displaying current weather information."""

from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Static
import httpx

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class WeatherCard(Card):
    """Weather card positioned at bottom left with icons and forecast."""
    
    DEFAULT_CSS = """
    #weather Static {
        text-align: left;
        padding: 1;
    }
    
    #weather .weather-now {
        text-style: bold;
        color: white;
    }
    """
    
    # Weather condition code to icon mapping (WMO Weather codes)
    # Using Nerd Font Weather Icons (single-width glyphs)
    WEATHER_ICONS = {
        0: "",   # Clear sky (nf-weather-day_sunny)
        1: "",   # Mainly clear (nf-weather-day_sunny)
        2: "",   # Partly cloudy (nf-weather-day_cloudy)
        3: "",   # Overcast (nf-weather-cloudy)
        45: "",  # Foggy (nf-weather-fog)
        48: "",  # Depositing rime fog (nf-weather-fog)
        51: "",  # Drizzle light (nf-weather-sprinkle)
        53: "",  # Drizzle moderate (nf-weather-sprinkle)
        55: "",  # Drizzle dense (nf-weather-rain)
        61: "",  # Rain slight (nf-weather-rain)
        63: "",  # Rain moderate (nf-weather-rain)
        65: "",  # Rain heavy (nf-weather-rain)
        71: "",  # Snow slight (nf-weather-snow)
        73: "",  # Snow moderate (nf-weather-snow)
        75: "",  # Snow heavy (nf-weather-snow)
        77: "",  # Snow grains (nf-weather-snow)
        80: "",  # Rain showers slight (nf-weather-showers)
        81: "",  # Rain showers moderate (nf-weather-showers)
        82: "",   # Rain showers violent (nf-weather-rain)
        85: "",  # Snow showers slight (nf-weather-snow)
        86: "",  # Snow showers heavy (nf-weather-snow)
        95: "",   # Thunderstorm (nf-weather-thunderstorm)
        96: "",   # Thunderstorm with slight hail (nf-weather-thunderstorm)
        99: "",   # Thunderstorm with heavy hail (nf-weather-thunderstorm)
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
                position=CardPosition.BOTTOM_LEFT,
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
            Weather icon glyph
        """
        return self.WEATHER_ICONS.get(code, "")  # nf-weather-thermometer
    
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
        lines.append("")
        lines.append(f" Wind: {wind} km/h")  # nf-weather-strong_wind
        lines.append(f" Humidity: {humidity}%")  # nf-weather-humidity
        
        # 3-day forecast
        daily = self._weather_data.get("daily", {})
        if daily:
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            codes = daily.get("weather_code", [])
            times = daily.get("time", [])
            
            if len(temps_max) >= 3 and len(times) >= 3:
                lines.append("")
                lines.append(" Forecast:")  # nf-weather-day_cloudy
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
