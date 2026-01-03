"""Tests for plugin initialization."""

import pytest
from smart_mirror import (
    Card,
    CardConfig,
    CardPosition,
    ClockCard,
    WeatherCard,
    GreeterCard,
)


def test_imports():
    """Test that all expected classes can be imported."""
    assert Card is not None
    assert CardConfig is not None
    assert CardPosition is not None
    assert ClockCard is not None
    assert WeatherCard is not None
    assert GreeterCard is not None


def test_card_position_values():
    """Test all CardPosition enum values."""
    positions = [
        CardPosition.TOP_LEFT,
        CardPosition.TOP_CENTER,
        CardPosition.TOP_RIGHT,
        CardPosition.MIDDLE_LEFT,
        CardPosition.MIDDLE_CENTER,
        CardPosition.MIDDLE_RIGHT,
        CardPosition.BOTTOM_LEFT,
        CardPosition.BOTTOM_CENTER,
        CardPosition.BOTTOM_RIGHT,
    ]
    
    assert len(positions) == 9
    
    # All should be unique
    values = [p.value for p in positions]
    assert len(values) == len(set(values))
