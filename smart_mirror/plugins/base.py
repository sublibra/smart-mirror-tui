"""Base plugin architecture for Smart Mirror cards."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import asyncio
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
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
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
        """
        pass
    
    async def start(self) -> None:
        """Start the card's update loop."""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def stop(self) -> None:
        """Stop the card's update loop."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self) -> None:
        """Internal update loop that runs the update method periodically."""
        while self._running:
            try:
                await self.update()
                self._last_update = datetime.now()
            except Exception as e:
                print(f"Error updating {self.name}: {e}")
            
            await asyncio.sleep(self.config.update_interval)
    
    def is_running(self) -> bool:
        """Check if the card is currently running."""
        return self._running
