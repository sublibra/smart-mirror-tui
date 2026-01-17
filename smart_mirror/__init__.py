"""Smart Mirror TUI application with plugin architecture."""

__version__ = "0.1.0"
__author__ = "Smart Mirror Developer"

from smart_mirror.core.app import SmartMirrorApp
from smart_mirror.plugins.base import Card, CardConfig, CardPosition
from smart_mirror.plugins.clock import ClockCard
from smart_mirror.plugins.greeter import GreeterCard
from smart_mirror.plugins.transport import TransportCard
from smart_mirror.plugins.weather import WeatherCard

__all__ = [
    "SmartMirrorApp",
    "Card",
    "CardConfig",
    "CardPosition",
    "ClockCard",
    "WeatherCard",
    "GreeterCard",
    "TransportCard",
]
