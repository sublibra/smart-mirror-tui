"""Tests for the base plugin architecture."""

import pytest
import asyncio
from textual.app import ComposeResult
from textual.widgets import Static
from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class SimpleTestCard(Card):
    """Simple test card for testing the base Card class."""
    
    DEFAULT_CSS = """
    #testcard {
        align: center middle;
    }
    """
    
    def __init__(self, config: CardConfig = None):
        if config is None:
            config = CardConfig(
                name="TestCard",
                position=CardPosition.MIDDLE_CENTER,
                update_interval=1,
            )
        super().__init__(config)
        self.update_count = 0
        self._widget: Static = None
    
    def compose(self) -> ComposeResult:
        """Yield test widget."""
        self._widget = Static("Test Card")
        yield self._widget
    
    async def update(self) -> None:
        self.update_count += 1
        if self._widget:
            self._widget.update(f"Test Card Update #{self.update_count}")


@pytest.fixture
def card():
    """Create a simple test card."""
    return SimpleTestCard()


def test_card_initialization(card):
    """Test basic card initialization."""
    assert card.name == "TestCard"
    assert card.position == CardPosition.MIDDLE_CENTER
    assert card.config.update_interval == 1
    assert not card.is_running()


def test_card_properties(card):
    """Test card properties."""
    assert card.name == "TestCard"
    assert card.position == CardPosition.MIDDLE_CENTER
    assert card.last_update is None


@pytest.mark.asyncio
async def test_card_compose(card):
    """Test card composition."""
    widgets = list(card.compose())
    assert len(widgets) == 1
    assert isinstance(widgets[0], Static)


@pytest.mark.asyncio
async def test_card_update(card):
    """Test card update."""
    await card.update()
    assert card.update_count == 1


@pytest.mark.asyncio
async def test_card_start_stop(card):
    """Test starting and stopping a card."""
    assert not card.is_running()
    
    await card.start()
    assert card.is_running()
    
    # Let it update once
    await asyncio.sleep(1.5)
    assert card.update_count >= 1
    
    await card.stop()
    assert not card.is_running()


def test_card_position_enum():
    """Test CardPosition enum values."""
    assert CardPosition.TOP_LEFT.value == "top_left"
    assert CardPosition.BOTTOM_RIGHT.value == "bottom_right"
    assert CardPosition.TOP_CENTER.value == "top_center"


def test_card_config_defaults():
    """Test CardConfig default values."""
    config = CardConfig(
        name="TestConfig",
        position=CardPosition.TOP_LEFT,
    )
    assert config.enabled is True
    assert config.update_interval == 60
    assert config.width == 40
    assert config.height == 10
    assert config.metadata == {}


def test_card_config_custom():
    """Test CardConfig with custom values."""
    metadata = {"key": "value"}
    config = CardConfig(
        name="CustomCard",
        position=CardPosition.MIDDLE_CENTER,
        enabled=False,
        update_interval=30,
        width=50,
        height=15,
        metadata=metadata,
    )
    assert config.enabled is False
    assert config.update_interval == 30
    assert config.width == 50
    assert config.height == 15
    assert config.metadata == metadata
