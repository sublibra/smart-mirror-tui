"""Smart Mirror plugins and cards."""

from smart_mirror.plugins.base import Card, CardConfig, CardPosition
from smart_mirror.plugins.clock import ClockCard
from smart_mirror.plugins.weather import WeatherCard
from smart_mirror.plugins.greeter import GreeterCard

__all__ = [
    "Card",
    "CardConfig",
    "CardPosition",
    "ClockCard",
    "WeatherCard",
    "GreeterCard",
]
