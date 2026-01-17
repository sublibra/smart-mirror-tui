"""Public transport departures card using Trafiklab Realtime API."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from textual.app import ComposeResult
from textual.widgets import Static

from smart_mirror.plugins.base import Card, CardConfig, CardPosition


class TransportCard(Card):
    """Display upcoming departures for a station with delay warnings.

    StationID can be found by querying:
        https://realtime-api.trafiklab.se/v1/stops/name/{station_name}?key={api_key}

    The response contains 'stop_groups' with 'id' field to use as TRANSPORT_STATION_ID.
    Get your API keys from: https://www.trafiklab.se/api/realtid-och-platsinformation
    """

    DEFAULT_CSS = """
    #transport {
        layout: vertical;
        align: center top;
    }

    #transport Static {
        text-align: left;
        padding: 1;
    }

    #transport .warning {
        color: orange;
    }
    """

    def __init__(
        self,
        config: Optional[CardConfig] = None,
        *,
        station_id: str = "",
        api_key: Optional[str] = None,
        update_interval: int = 60,
        delay_threshold: int = 60,
        time_window: int = 60,
        max_departures: int = 6,
    ):
        if config is None:
            config = CardConfig(
                name="Transport",
                position=CardPosition.BOTTOM_CENTER,
                update_interval=update_interval,
                width=60,
                height=12,
                border_style="yellow",
                text_align="left",
            )

        super().__init__(config)
        self.station_id = station_id
        self.api_key = api_key
        self.delay_threshold = delay_threshold
        self.time_window = time_window
        self.max_departures = max_departures

        self._departures: List[Dict[str, Any]] = []
        self._list_widget: Optional[Static] = None
        self._last_render: str = ""
        self._now_provider = datetime.now
        self.log("TransportCard initialized", station_id=station_id)

    def compose(self) -> ComposeResult:
        """Compose the departures view."""
        self.log("Composing TransportCard UI...")
        self._list_widget = Static(
            "Initializing transport card...",
        )
        yield self._list_widget

    async def update(self) -> None:
        """Fetch and display departures."""
        if not self.station_id or not self.api_key:
            self._set_message(
                "Transport card not configured: set TRANSPORT_STATION_ID and TRANSPORT_API_KEY."
            )
            return
        self.log("Updating TransportCard departures...")
        try:
            data = await self._fetch_departures()
            self._set_message("Parsing departures...")
            self._departures = self._parse_departures(data)
            if not self._departures:
                self._set_message("No upcoming departures in the next 60 minutes.")
                return

            message = self._format_departures(self._departures)
            self._set_message(message)
        except Exception as exc:  # pragma: no cover - safety net
            self._set_message(f"Error: {exc}")

    async def _fetch_departures(self) -> Dict[str, Any]:
        """Call Trafiklab Realtime API departure endpoint."""
        url = f"https://realtime-api.trafiklab.se/v1/departures/{self.station_id}"
        params = {"key": self.api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _parse_departures(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten response into a list of departures sorted by expected time."""
        departures = payload.get("departures", []) if payload else []
        items: List[Dict[str, Any]] = []

        for entry in departures or []:
            parsed = self._parse_entry(entry)
            if parsed:
                items.append(parsed)

        items.sort(key=self._sort_key)
        return items

    def _parse_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single departure entry, ignoring invalid records."""
        if not entry or entry.get("canceled"):
            return None

        # Trafiklab returns ISO 8601 formatted datetimes
        expected = self._parse_time(entry.get("realtime"))
        timetable = self._parse_time(entry.get("scheduled"))
        route = entry.get("route", {})

        return {
            "line": str(route.get("designation") or route.get("name", "")),
            "destination": str(route.get("direction", "")),
            "expected": expected,
            "timetable": timetable,
            "delay_seconds": entry.get("delay", 0),
            "transport_mode": str(route.get("transport_mode", "")).upper(),
        }

    def _parse_time(self, value: Any) -> Optional[datetime]:
        """Parse an ISO timestamp into a timezone-aware datetime."""
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    def _sort_key(self, item: Dict[str, Any]) -> datetime:
        """Sort by expected time, fallback to timetable, then now."""
        fallback = self._now_provider(timezone.utc)
        return item.get("expected") or item.get("timetable") or fallback

    def _format_departures(self, departures: List[Dict[str, Any]]) -> str:
        """Build a multiline string for the departures list."""
        lines: List[str] = []
        for dep in departures[: self.max_departures]:
            line = self._format_line(dep)
            lines.append(line)
        return "\n".join(lines)

    def _format_line(self, dep: Dict[str, Any]) -> str:
        """Format a single departure line."""
        mode = self._mode_label(dep.get("transport_mode"))
        line_no = dep.get("line", "")
        destination = dep.get("destination", "")
        time_part = self._format_time(dep.get("expected"))
        delay_part = self._format_delay(dep.get("delay_seconds", 0))
        parts = [mode, line_no, destination, "-", time_part]
        if delay_part:
            parts.append(delay_part)
        return " ".join(str(p) for p in parts if p)

    def _format_time(self, expected: Optional[datetime]) -> str:
        """Format expected time into a human-readable string."""
        if expected:
            now = self._now_provider(expected.tzinfo or timezone.utc)
            delta = (expected - now).total_seconds()
            if delta < -60:
                return "left"
            if delta < 60:
                return "now"
            minutes = math.ceil(delta / 60)
            clock = expected.strftime("%H:%M")
            return f"in {minutes}m ({clock})"
        return "n/a"

    def _format_delay(self, delay_seconds: int) -> str:
        """Return warning string when delay exceeds threshold."""
        if not delay_seconds or abs(delay_seconds) < self.delay_threshold:
            return ""

        minutes = int(round(delay_seconds / 60))
        sign = "+" if minutes >= 0 else "-"
        return f"[WARN {sign}{abs(minutes)}m]"

    def _mode_label(self, mode: str) -> str:
        """Return short label for transport mode."""
        labels = {
            "BUS": "🚍",
            "METRO": "Ⓜ️",
            "TRAIN": "🚆",
            "TRAM": "🚊",
            "BOAT": "🛥",
            "TAXI": "🚕",
        }
        return labels.get(mode or "", mode or "")

    def _set_message(self, message: str) -> None:
        """Update widget text and remember last render for tests."""
        self._last_render = message
        self.log("TransportCard", message)
        if self._list_widget:
            self._list_widget.update(message)

    @staticmethod
    async def lookup_station(station_name: str, api_key: str) -> Dict[str, Any]:
        """Look up station ID by name using Trafiklab Stop Lookup API.

        Args:
            station_name: Name of the station (e.g., "Stehag", "Central")
            api_key: Trafiklab API key

        Returns:
            Response from the API with matching stations

        Example:
            result = await TransportCard.lookup_station("Stehag", "your-api-key")
            # Pick the station ID from result and set TRANSPORT_STATION_ID
        """
        url = f"https://realtime-api.trafiklab.se/v1/stops/name/{station_name}"
        params = {"key": api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
