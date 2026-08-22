"""Tests for the Qlik menu card and HTML parser."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smart_mirror.plugins.qlik_menu import QlikMenuCard, parse_qlik_menu

SAMPLE_HTML = """
<html>
  <body>
    <h3 class="elementor-heading-title elementor-size-default">Öppettider</h3>
    <h3 class="elementor-heading-title elementor-size-default">Måndag</h3>
    <ul class="elementor-price-list">
      <li class="elementor-price-list-item">
        <span class="elementor-price-list-title">Local</span>
        <span class="elementor-price-list-price">105:-</span>
        <p class="elementor-price-list-description">Pannbiff med stekt lök</p>
      </li>
      <li class="elementor-price-list-item">
        <span class="elementor-price-list-title">Green</span>
        <span class="elementor-price-list-price">105:-</span>
        <p class="elementor-price-list-description">Betor, quinoa, linser</p>
      </li>
    </ul>
    <h3 class="elementor-heading-title elementor-size-default">Tisdag</h3>
    <ul class="elementor-price-list">
      <li class="elementor-price-list-item">
        <span class="elementor-price-list-title">World Wide</span>
        <p class="elementor-price-list-description">Pulled pork burrito</p>
      </li>
    </ul>
  </body>
</html>
"""


def test_parse_qlik_menu_skips_non_day_headings():
    menu = parse_qlik_menu(SAMPLE_HTML)

    assert [item["day"] for item in menu] == ["Måndag", "Tisdag"]
    assert menu[0]["dishes"] == [
        "Local: Pannbiff med stekt lök",
        "Green: Betor, quinoa, linser",
    ]
    assert menu[1]["dishes"] == ["World Wide: Pulled pork burrito"]


def test_parse_qlik_menu_empty_html():
    assert parse_qlik_menu("<html></html>") == []


def test_qlik_menu_card_initialization():
    card = QlikMenuCard()
    assert card.name == "QlikMenu"
    assert card.config.update_interval == 7200


@pytest.mark.asyncio
async def test_qlik_menu_card_compose():
    card = QlikMenuCard()
    widgets = list(card.compose())
    assert len(widgets) == 1
    assert card._qlik_menu_widget is not None


@pytest.mark.asyncio
async def test_get_menu_uses_html_parser():
    card = QlikMenuCard()
    response = MagicMock()
    response.text = SAMPLE_HTML
    response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("smart_mirror.plugins.qlik_menu.httpx.AsyncClient", return_value=mock_client):
        menu = await card._get_menu()

    assert len(menu) == 2
    assert menu[0]["day"] == "Måndag"
    mock_client.get.assert_awaited_once()


def test_format_menu_shows_upcoming_days():
    card = QlikMenuCard()
    menu = parse_qlik_menu(SAMPLE_HTML)

    fake_now = MagicMock()
    fake_now.weekday.return_value = 0  # Monday
    fake_now.hour = 8

    with patch("smart_mirror.plugins.qlik_menu.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now
        formatted = card._format_menu(menu)

    assert "Måndag" in formatted
    assert "Local: Pannbiff med stekt lök" in formatted
    assert "Tisdag" in formatted
