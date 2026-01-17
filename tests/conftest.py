import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    """Mock hardware-specific services that are initialized in the app."""
    monkeypatch.setattr("smart_mirror.core.app.PIRSensor", MagicMock())
    monkeypatch.setattr("smart_mirror.core.app.ScreenManager", MagicMock())
