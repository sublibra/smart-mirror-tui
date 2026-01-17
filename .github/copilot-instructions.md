# Copilot Instructions for Smart Mirror TUI Project

## Project Overview

This is a Python-based smart mirror application with a TUI (Terminal User Interface) built using the Textual library. The project follows a plugin architecture where individual cards (widgets) can be added to display various information.

## Key Principles

### Architecture
- **Plugin-Based**: All cards inherit from `Card` base class in `smart_mirror/plugins/base.py`
- **Widget-Driven**: Cards compose Textual widgets (Digits, Static, etc.) instead of rendering strings
- **Async**: Heavy use of asyncio for concurrent updates
- **Configuration-Driven**: Environment variables and CardConfig objects control behavior
- **Type-Hinted**: Code uses Python type hints throughout
- **CSS-Styled**: Each card owns its CSS in `DEFAULT_CSS` class property

### Code Organization
- `smart_mirror/core/app.py` - Main Textual application orchestration
- `smart_mirror/core/widgets.py` - CardWidget container that wraps Card plugins
- `smart_mirror/plugins/` - Card implementations
- `smart_mirror/plugins/base.py` - Abstract Card class and CardConfig
- `tests/` - Comprehensive test suite

### Testing
- Use pytest with pytest-asyncio for async tests
- Test files mirror the module structure: `tests/test_*.py`
- All async functions should be tested with `@pytest.mark.asyncio`

## When Making Changes

### Adding New Features
1. **Create Cards**: Subclass `Card` in `smart_mirror/plugins/`
2. **Implement `compose()`**: Yield Textual widgets (Digits, Static, etc.)
3. **Implement `update()`**: Update widget content periodically
4. **Add CSS**: Define `DEFAULT_CSS` class property for styling
5. **Register Cards**: Add to `SmartMirrorApp._initialize_plugins()` or call `app.register_card()`
6. **Write Tests**: Add test cases in `tests/test_*.py`
7. **Update Config**: Add environment variables to `.env.example`

### Code Style
- Use `black` for formatting (100 char line length)
- Use `ruff` for linting
- Use `mypy` for type checking
- Follow async/await patterns throughout

### Logging
- Cards should log through Textual's logging interface, not the standard `logging` module.
- `CardWidget` injects `card.set_logger(self.log)` during `on_mount`; call `self.log(...)` inside cards.
- Keep messages concise; include key context via kwargs (e.g., `self.log("Fetching", url=url)`).
- Avoid bare `print`; the fallback in `Card.log` is only for early bootstrap.

### Async Patterns
```python
# Always use async methods
async def update(self) -> None:
    # Avoid blocking I/O
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    # Update widgets directly
    if self._widget:
        self._widget.update(data)

# Use asyncio.sleep not time.sleep
await asyncio.sleep(1.0)
```

### Card Implementation Template
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
                position=CardPosition.TOP_LEFT,
                update_interval=60,
                width=40,
                height=10,
            )
        super().__init__(config)
        self._widget: Optional[Static] = None
        self._data = None
    
    def compose(self) -> ComposeResult:
        # Yield Textual widgets
        self._widget = Static("Loading...")
        yield self._widget
    
    async def update(self) -> None:
        # Fetch/update data
        self._data = await self._fetch_data()
        # Update widget directly
        if self._widget:
            self._widget.update(f"Data: {self._data}")
    
    async def _fetch_data(self):
        # Helper methods as needed
        pass
```

## Dependencies & Versions

### Production
- `textual>=0.87.0` - TUI framework with widgets, CSS, reactive updates
- `rich>=13.0.0` - Text rendering and styling (used by Textual)
- `httpx>=0.25.0` - Async HTTP requests
- `python-dotenv>=1.0.0` - Environment management

### Development (installed with `uv sync --all-extras`)
- `pytest>=7.0.0` - Testing
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage reports
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Widget Types

### Available Textual Widgets
- **Digits** - Large digital display (perfect for clocks)
- **Static** - Text display with Rich markup support
- **Container** - Layout container for grouping widgets
- **Vertical/Horizontal** - Directional containers

### Widget Usage Patterns
```python
# Largwith live reload for CSS changes
textual run --dev smart_mirror

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=smart_mirror

# Format code
uv run black smart_mirror tests

# Lint code
uv run ruff check smart_mirror tests

# Type check
uv run mypy smart_mirror
```

## Styling with CSS

Each card owns its CSS through the `DEFAULT_CSS` class property:

```python
class MyCard(Card):
    DEFAULT_CSS = """
    #mycard {
        align: center middle;
        layout: vertical;
    }
    
    #mycard Digits {
        width: 100%;
        text-align: center;
        color: cyan;
    }
    
    #mycard Static {
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }
    """
```

### CSS Guidelines
- *Implement `compose()` to yield Textual widgets
3. Implement `update()` to refresh widget content
4. Add `DEFAULT_CSS` for card styling
5. Add to `smart_mirror/plugins/__init__.py` exports
6. Create `tests/test_mycard.py` with comprehensive tests
7. Update `.env.example` with any new config variables
8. Register in `SmartMirrorApp._initialize_plugins()` if default

### Text Sizing
Use appropriate Textual widgets for sizing:
- **Large text**: Use `Digits` widget for numbers
- **Normal text**: Use `Static` widget
- **Rich markup**: Use `[bold]`, `[dim]`, etc. in Static widgets
- **NO character spacing**: Don't use `' '.join(text)` hacks

### Debug an Issue
```bash
# Run specific test with verbose output
uv run pytest tests/test_app.py::test_name -vv

# Run with print statements visible
uv run pytest tests/test_app.py -s

# Run with pdb debugging
uv run pytest tests/test_app.py --pdb

# Use Textual console for live debugging
textual console

# Run tests with coverage
uv run pytest --cov=smart_mirror

# Format code
uv run black smart_mirror tests

# Lint code
uv run ruff check smart_mirror tests

# Type check
uv run mypy smart_mirror
```

## Common Tasks

### Fix Code Style Issues
```bash
uv run black smart_mirror tests
uv run ruff check --fix smart_mirror tests
```

### Add a New Card
1. Create `smart_mirror/plugins/mycard.py` with Card subclass
2. Add to `smart_mirror/plugins/__init__.py` exports
3. Create `tests/test_mycard.py` with comprehensive tests
4. Update `.env.example` with any new config variables
5. Register in `SmartMirrorApp._initialize_plugins()` if default

### Debug an Issue
```bash
# Run specific test with verbose output
uv run pytest tests/test_app.py::test_name -vv

# Run with print statements visible
uv run pytest tests/test_app.py -s

# Run with pdb debugging
uv run pytest tests/test_app.py --pdb
```

Remember that textual will capture stdout/stderr.

## PIR Sensor Integration

The application supports face recognition integration via the `set_user_name()` method:

```python
app Widget wrapper** → `smart_mirror/core/widgets.py`
- **Tests** → `tests/` (mirror the package structure)
- **Configuration** → `.env` / `.env.example`
- **Documentation** → `README.md` / `.github/copilot-instructions.md` / `docs/`

## Current Card Implementations

### ClockCard (`smart_mirror/plugins/clock.py`)
- **Widget**: `Digits` for time display, `Static` for date
- **Update**: Every 1 second
- **Features**: Large digital clock with date subtitle
- **CSS**: Centered layout with vertical stacking

### GreeterCard (`smart_mirror/plugins/greeter.py`)
- **Widget**: `Static` with Rich markup
- **Update**: Every 5 minutes
- **Features**: Time-based greeting with user name
- **CSS**: Borderless, centered yellow text

### WeatherCard (`smart_mirror/plugins/weather.py`)
- **Widget**: `Static` with Rich markup
- **Update**: Every 5 minutes
- **Features**: Current weather with emoji icons, and 3-day forecast
- **API**: Open-Meteo (free, no auth required)
- **CSS**: Left-aligned with bold "Now" section
- **Icons**: Uses Nerd Font Weather Icons for proper terminal rendering

## Raspberry Pi Deployment

The application is designed to run on Raspberry Pi with:
- **Compositor**: cage (Wayland compositor for kiosk mode)
- **Terminal**: foot (modern terminal with excellent Unicode/Nerd Font support)
- **Font**: JetBrains Mono Nerd Font for weather icons and glyphs, Noto Color Emoji for emojis
- **Autostart**: systemd service for boot-time startup

### Terminal Requirements
- Use cage + foot for proper Nerd Font glyph rendering
- Avoid fbterm (limited wide glyph and truecolor support)
- Ensure `TERM=foot` environment variable is set
- Configure foot.ini with Nerd Font and proper fallbacks

### Key Files
- `install-service.sh` - Automated installation script
- `smart-mirror.service.example` - systemd service template
- `start-mirror.sh` - Startup script with screen rotation
- `foot.ini` - Terminal configuration with Nerd Font settings

The greeter card automatically updates based on:
- Time of day (Good morning, afternoon, evening)
- User name (via face recognition or manual setting)

## Example Test Pattern

```python
@pytest.mark.asyncio
async def test_my_card_compose():
    card = MyCard()
    widgets = list(card.compose())
    assert len(widgets) > 0
    assert isinstance(widgets[0], Static)

@pytest.mark.asyncio
async def test_my_card_update():
    card = MyCard()
    list(card.compose())  # Initialize widgets
    await card.update()
    assert card._widget is not None
```

## Performance Considerations

- Each card runs its own update loop asynchronously
- Update intervals are configurable per card (default 60s)
- Cards update their widgets directly (no string parsing overhead)
- Textual handles rendering optimization automatically
- Use async I/O for all network requests
- Minimize blocking operations

## Known Limitations & Future Work

- Layout is a simple 3x3 grid
- No interactive input yet (planned for future)
- Consider adding more widget types (charts, graphs, etc.)
- REST API planned for remote control
- Consider adding config file support (YAML/TOML)

## Architecture Changes (January 2026)

**Major refactor from string rendering to widget composition:**
- ❌ **Old**: Cards rendered strings, CardWidget parsed and displayed them
- ✅ **New**: Cards compose Textual widgets directly, better performance and flexibility

**Key changes:**
- `Card.render() → Card.compose()` - Now yields widgets instead of strings
- `CardWidget` is now a `Container` that composes child widgets
- Text sizing through proper widgets (`Digits`) not character spacing
- Rich markup supported in `Static` widgets via `update()` method
- Removed `text_size` from CardConfig (use appropriate widgets instead
@pytest.mark.asyncio
async def test_my_card_render():
    card = MyCard()
    rendered = await card.render()
    assert len(rendered) > 0
```

## Performance Considerations

- Each card runs its own update loop asynchronously
- Update intervals are configurable per card (default 60s)
- Display refreshes at `DISPLAY_REFRESH_RATE` (default 1 FPS)
- Use async I/O for all network requests
- Minimize blocking operations in render methods

## Known Limitations & Future Work

- Layout is simple (top, middle, bottom × left, center, right)
- No interactive input yet (planned for future)
- Textual integration planned for more advanced widgets
- REST API planned for remote control
- Consider adding config file support (YAML/TOML)

## Useful Resources

- **Rich Documentation**: https://rich.readthedocs.io/
- **Textual Documentation**: https://textual.textualize.io/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **AsyncIO Guide**: https://docs.python.org/3/library/asyncio.html
- **HTTPX Docs**: https://www.python-httpx.org/

## Questions or Issues?

When asking for changes:
- Be specific about which cards/modules are affected
- Provide test cases or expected behavior
- Consider backward compatibility
- Update tests and documentation along with code changes
