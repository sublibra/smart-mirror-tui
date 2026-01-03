# Smart Mirror TUI

A colorful Terminal User Interface (TUI) smart mirror built in Python with a plugin architecture for extensible "cards" that display useful information. Built with Textual for a smooth, flicker-free experience.

## Features

- 🎨 **Professional TUI Display** - Powered by Textual framework
- 🚀 **Flicker-Free Updates** - Only refreshes changed widgets
- 📐 **Perfect Grid Layout** - 3x3 grid with aligned cards
- 🔌 **Plugin Architecture** - Easily add new cards/widgets
- ⏱️ **Configurable Update Intervals** - Each card has its own refresh rate
- 🕐 **Example Cards**:
  - **Clock**: Large digital clock with date subtitle (using Textual Digits widget)
  - **Weather**: Current weather with emoji icons and 3-day forecast
  - **Greeter**: Personalized time-based greetings with user name support
- 📐 **Flexible Layout** - Position cards anywhere on the display
- 🧪 **Comprehensive Tests** - Full test suite with pytest
- 🔧 **UV Package Management** - Fast Python package management with uv

## Project Structure

```
smart-mirror-tui/
├── smart_mirror/          # Main package
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app.py        # Main Textual application
│   │   └── widgets.py    # CardWidget container
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base.py       # Base plugin architecture
│   │   ├── clock.py      # Clock card
│   │   ├── weather.py    # Weather card
│   │   └── greeter.py    # Greeter card
│   ├── __init__.py
│   └── __main__.py       # CLI entry point
├── tests/                # Test suite
│   ├── test_app.py
│   ├── test_plugins.py
│   ├── test_cards.py
│   ├── test_imports.py
│   └── conftest.py
├── pyproject.toml        # Project configuration
├── .env.example          # Environment variables template
├── .gitignore
└── README.md
```

## Installation

### Prerequisites
- Python 3.10 or higher
- `uv` package manager ([install uv](https://docs.astral.sh/uv/))

### Setup

1. Clone the repository:
```bash
cd /home/jonash/git/smart-mirror-tui
```

2. Create a `.env` file from the template:
```bash
cp .env.example .env
```

3. Install dependencies:
```bash
uv sync
```

## Configuration

Edit `.env` to customize your smart mirror:

```env
# Display Settings
DISPLAY_WIDTH=120          # Terminal width
DISPLAY_HEIGHT=30          # Terminal height
REFRESH_RATE=1             # Updates per second

# Weather API Settings
WEATHER_LATITUDE=52.5200   # Your latitude
WEATHER_LONGITUDE=13.4050  # Your longitude

# User Configuration
DEFAULT_USER_NAME=Mirror User  # Default greeting name
```

## Usage

### Run the Application

```bash
uv run smart_mirror
```

Or directly:
```bash
python -m smart_mirror
```

### Running Tests

```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=smart_mirror
```

Run specific test file:
```bash
uv run pytest tests/test_app.py -v
```

## Creating Custom Cards

To create a new card/plugin, inherit from the `Card` base class:

```python
from textual.app import ComposeResult
from textual.widgets import Static
from smart_mirror.plugins.base import Card, CardConfig, CardPosition

class MyCard(Card):
    DEFAULT_CSS = """
    #mycard {
        align: center middle;
    }
    
    #mycard Static {
        text-align: center;
        color: cyan;
    }
    """
    
    def __init__(self, config=None):
        if config is None:
            config = CardConfig(
                name="MyCard",
                position=CardPosition.TOP_RIGHT,
                update_interval=60,
                width=40,
                height=10,
            )
        super().__init__(config)
        self._widget = None
    
    def compose(self) -> ComposeResult:
        """Yield Textual widgets to display."""
        self._widget = Static("Loading...")
        yield self._widget
    
    async def update(self) -> None:
        """Fetch/update data and refresh widgets."""
        data = await self._fetch_data()
        if self._widget:
            self._widget.update(f"Data: {data}")
    
    async def _fetch_data(self):
        """Helper method to fetch data."""
        return "example data"

# Register with the app
app = SmartMirrorApp()
app.register_card(MyCard())
```

## Plugin Architecture

### Card Base Class

All cards inherit from `Card` and must implement:

- `compose()`: Yield Textual widgets (Digits, Static, etc.) to display
- `async update()`: Periodically fetch/update the card's data and refresh widgets
- `DEFAULT_CSS`: Class property defining the card's CSS styling

### CardConfig

Configure each card with:
- `name`: Unique identifier
- `position`: Where to display (top/middle/bottom × left/center/right)
- `enabled`: Enable/disable the card
- `update_interval`: Seconds between updates
- `width`: Card width in characters
- `height`: Card height in characters
- `show_border`: Whether to show card border (default: True)
- `show_title`: Whether to show card title (default: True)
- `border_style`: Border color/style (e.g., "cyan", "yellow")
- `title_style`: Title color/style
- `text_color`: Default text color
- `text_align`: Text alignment ("left", "center", "right")
- `metadata`: Custom configuration data

### CardPosition

Available positions:
- `TOP_LEFT`, `TOP_CENTER`, `TOP_RIGHT`
- `MIDDLE_LEFT`, `MIDDLE_CENTER`, `MIDDLE_RIGHT`
- `BOTTOM_LEFT`, `BOTTOM_CENTER`, `BOTTOM_RIGHT`

## Integration with PIR Sensor

The smart mirror can be updated with recognized faces from a PIR sensor integration:

```python
app = SmartMirrorApp()

# When a face is recognized, update the greeter
app.set_user_name("Alice")
```

The greeter card will then display personalized greetings with the user's name.

## Dependencies

### Core Dependencies
- **textual** (>=0.87.0) - Professional TUI framework with widgets, CSS, and reactive updates
- **rich** (>=13.0.0) - Text rendering and styling (used by Textual)
- **httpx** (>=0.25.0) - Async HTTP client for weather data
- **python-dotenv** (>=1.0.0) - Environment configuration

### Development Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **ruff** - Fast Python linter
- **mypy** - Static type checking

## Development

### Run with Live CSS Reload
```bash
textual run --dev smart_mirror
```

### Open Textual Console for Debugging
```bash
textual console
```

### Format Code
```bash
uv run black smart_mirror tests
```

### Lint Code
```bash
uv run ruff check smart_mirror tests
```

### Type Check
```bash
uv run mypy smart_mirror
```

## Future Enhancements

- [x] Advanced layout system (using Textual Grid)
- [x] Widget-based architecture with Textual
- [x] CSS styling for cards
- [ ] More example cards (stocks, news, calendar, etc.)
- [ ] Configuration file support (YAML/TOML)
- [ ] Card animation support
- [ ] REST API for remote control
- [ ] Database for persistence
- [ ] Docker support
- [ ] Raspberry Pi optimization

## License

MIT

## Contributing

Contributions are welcome! Please:
1. Write tests for new features
2. Follow the code style (black + ruff)
3. Update documentation
4. Submit a pull request

## Troubleshooting

### Cards not updating?
- Check `DISPLAY_REFRESH_RATE` in `.env`
- Verify `update_interval` in card configuration
- Check application logs

### Weather not working?
- Verify internet connection
- Check latitude/longitude in `.env`
- Weather API is free (Open-Meteo) - no key needed

### Permission denied when running?
```bash
chmod +x smart_mirror
```

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
