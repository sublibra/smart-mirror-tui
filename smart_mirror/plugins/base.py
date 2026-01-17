"""Base plugin architecture for Smart Mirror cards."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from textual.app import ComposeResult


class CardPosition(str, Enum):
    """Card positioning on the mirror display."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    MIDDLE_CENTER = "middle_center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class CardConfig:
    """Configuration for a card/plugin."""

    name: str
    position: CardPosition
    enabled: bool = True
    update_interval: int = 60  # seconds
    width: int = 40
    height: int = 10
    show_border: bool = True
    show_title: bool = True
    border_style: str = "blue"
    title_style: str = "bold cyan"
    text_color: str = "white"
    text_align: str = "center"  # left, center, right
    metadata: dict = field(default_factory=dict)


class Card(ABC):
    """Base class for all smart mirror cards/plugins."""

    # Default CSS for this card type (can be overridden by subclasses)
    DEFAULT_CSS = ""

    def __init__(self, config: CardConfig):
        """Initialize a card with its configuration.

        Args:
            config: CardConfig instance for this card
        """
        self.config = config
        self._last_update: Optional[datetime] = None
        self._logger: Optional[Callable[..., Any]] = None

    def set_logger(self, logger: Callable[..., Any]) -> None:
        """Inject a logging callable (typically Textual's log)."""
        self._logger = logger

    def log(self, *objects: Any, level: str = "info", **kwargs: Any) -> None:
        """Log via the injected logger or fall back to stdout."""
        if self._logger:
            self._logger(*objects, level=level, **kwargs)
        else:
            extras = f" {kwargs}" if kwargs else ""
            print(*objects, extras)

    @property
    def name(self) -> str:
        """Return the card name."""
        return self.config.name

    @property
    def position(self) -> CardPosition:
        """Return the card position."""
        return self.config.position

    @property
    def last_update(self) -> Optional[datetime]:
        """Return the last update time."""
        return self._last_update

    @abstractmethod
    def compose(self) -> ComposeResult:
        """Compose the card's widgets.

        Yields:
            Textual widgets for this card
        """
        pass

    @abstractmethod
    async def update(self) -> None:
        """Update the card's internal data.

        This method is called periodically based on update_interval.
        CardWidget handles calling this method at the appropriate interval.
        """
        pass
