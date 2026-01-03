# CSS Styling Guide for Smart Mirror TUI

The Smart Mirror TUI uses Textual's powerful CSS system for styling cards and layouts. **Each plugin owns its own CSS**, maintaining the separation of concerns in the plugin architecture.

## Plugin Architecture & CSS

### How It Works

1. **Each card defines its CSS** in its plugin file using `DEFAULT_CSS`
2. **App loads all card CSS** during initialization via `_load_card_css()`
3. **Global layout CSS** remains in [app.py](../smart_mirror/core/app.py)

### Card CSS Example

```python
# In smart_mirror/plugins/clock.py
class ClockCard(Card):
    """Clock card with its own styling."""
    
    DEFAULT_CSS = """
    #clock {
        text-style: bold;
        color: cyan;
    }
    
    #clock Static {
        text-align: center;
        content-align: center middle;
    }
    """
```

## Creating a New Card with CSS

When creating a new plugin, add CSS directly to your card class:


```python
# smart_mirror/plugins/mycustom.py
from smart_mirror.plugins.base import Card, CardConfig, CardPosition

class MyCustomCard(Card):
    """Custom card with its own styling."""
    
    DEFAULT_CSS = """
    #mycustom {
        color: green;
        border: double green;
        text-style: bold italic;
    }
    
    #mycustom Static {
        text-align: center;
        content-align: center middle;
    }
    """
    
    def __init__(self, config=None):
        if config is None:
            config = CardConfig(
                name="MyCustom",  # Must match CSS ID (lowercase)
                position=CardPosition.MIDDLE_CENTER,
                update_interval=60,
            )
        super().__init__(config)
    
    async def render(self) -> str:
        return "My Custom Content"
    
    async def update(self) -> None:
        pass
```

## Current Card Styles

### Clock Card ([clock.py](../smart_mirror/plugins/clock.py))
```css
#clock {
    text-style: bold;
    color: cyan;
}

#clock Static {
    text-align: center;
    content-align: center middle;
}
```

### Greeter Card ([greeter.py](../smart_mirror/plugins/greeter.py))
```css
#greeter {
    border: none;
    padding: 0;
}

#greeter Static {
    text-style: bold;
    color: yellow;
    text-align: center;
    content-align: center middle;
}
```

### Weather Card ([weather.py](../smart_mirror/plugins/weather.py))
```css
#weather {
    color: white;
    border: solid blue;
}

#weather Static {
    text-align: left;
}
```

## CSS Naming Convention

- **Card ID**: Lowercase version of `config.name` (e.g., "Clock" → `#clock`)
- **Position Class**: Based on `CardPosition` enum (e.g., `.top-left`, `.bottom-center`)

## Available CSS Properties

### Text Styling
```css
#clock {
    color: cyan;                    /* Text color */
    text-style: bold;              /* bold, italic, underline */
    text-align: center;            /* left, center, right */
    content-align: center middle;  /* horizontal vertical */
}
```

### Border & Background
```css
#weather {
    border: solid blue;            /* none, solid, dashed, double */
    background: black;             /* Background color */
    padding: 1 2;                  /* top/bottom left/right */
}
```

### Layout & Size
```css
#greeter {
    width: 100%;                   /* Width in cells or percentage */
    height: 50%;                   /* Height */
    column-span: 2;                /* Span multiple columns */
    row-span: 1;                   /* Span multiple rows */
}
```

## Text Sizing

Text size is controlled through Rich markup in each card's `render()` method. Use character spacing and Rich styles for larger text:

```python
# In your card's render() method
async def render(self) -> str:
    # Add spaces between characters for larger appearance
    text = "12:34:56"
    large_text = ' '.join(text)  # "1 2 : 3 4 : 5 6"
    
    # Combine with Rich markup for styling
    return f"[bold cyan]{large_text}[/bold cyan]"
```

### Common Rich Markup Patterns

**Large text with character spacing:**
```python
message = "Hello"
large = ' '.join(message)  # "H e l l o"
return f"[bold]{large}[/bold]"
```

**Multiple sizes in one render:**
```python
return "[bold cyan]L A R G E[/bold cyan]\\n[dim]small text[/dim]"
```

**Color and style combinations:**
```python
return "[bold yellow]G o o d   M o r n i n g[/bold yellow]"
```

## Global Layout (app.py)

The main application only contains layout CSS. Card-specific styles belong in plugin files:

```python
# smart_mirror/core/app.py
class SmartMirrorApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        background: $surface;
    }
    
    /* Position classes for layout */
    .top-left { column-span: 1; row-span: 1; }
    .bottom-center { column-span: 1; row-span: 1; }
    /* ... etc ... */
    """
```

## Modifying Existing Card Styles

To change a card's appearance, edit its plugin file:

1. Open the card's plugin file (e.g., [clock.py](../smart_mirror/plugins/clock.py))
2. Modify the `DEFAULT_CSS` string
3. Restart the app to see changes

**Example:** Making the clock green with different styling:
```python
# In smart_mirror/plugins/clock.py
DEFAULT_CSS = """
#clock {
    text-style: bold;
    color: green;
    border: heavy green;
}

#clock Static {
    text-align: center;
    content-align: center middle;
}
"""

# In the render() method for larger text:
async def render(self) -> str:
    time_str = "12:34:56"
    large_time = ' '.join(time_str)  # Add spacing
    return f"[bold green]{large_time}[/bold green]"
```

## Advanced Examples

### Large Clock with Custom Colors
```css
#clock {
    content-align: center middle;
}
```border: heavy cyan;
    background: $boost;
    text-style: bold;
    color: $accent;
}

#clock Static {
    content-align: center middle;
}
```

```python
# In clock.py render() for large text:
async def render(self) -> str:
    time_str = self._current_time.strftime("%H:%M:%S")
    large_time = ' '.join(time_str)  # Character spacing
    return f"[bold cyan]{large_time}[/bold cyan]"
### Weather Card with Grid Layout
```css
#weather {
    layout: grid;
    grid-size: 2;
    grid-gutter: 1;
    border: double blue;
    padding: 2;
}
```

### Borderless Cards
```css
#greeter, #clock {
    border: none;
    padding: 0;
}
```

### Responsive Sizing
```css
.top-left, .top-right {
    height: 30%;
}

.middle-center {
    height: 40%;
    width: 80%;
}
```

## Color Names

Textual supports many color formats:
- Named colors: `red`, `green`, `blue`, `cyan`, `yellow`, `white`, etc.
- Hex colors: `#ff0000`, `#00ff00`
- RGB: `rgb(255, 0, 0)`
- Theme variables: `$primary`, `$accent`, `$boost`, `$warning`, `$error`

## Text Styles

Combine with spaces:
```css
text-style: bold italic;
text-style: bold underline;
text-style: italic reverse;
```

## Tips

1. **CSS in plugins**: Keep card styling in plugin files for modularity
2. **CSS in app.py**: Only global layout and grid styling
3. **Use IDs for specific cards**: `#clock`, `#weather`, `#greeter`
4. **Use classes for positions**: `.top-left`, `.bottom-center`
5. **Target child elements**: `#clock Static` targets Static widgets inside clock
6. **Test incrementally**: Change one property at a time
7. **Plugin isolation**: Each plugin is self-contained with its own CSS

## Resources

- [Textual CSS Documentation](https://textual.textualize.io/guide/CSS/)
- [Textual Styles Reference](https://textual.textualize.io/styles/)
- [Textual Color Reference](https://textual.textualize.io/guide/design/#colors)

## Troubleshooting

**Styles not applying?**
- Check widget ID matches card name (lowercase)
- Ensure CSS syntax is correct (no semicolons at end of blocks)
- Try `textual console` for live debugging
- Restart the app after CSS changes

**Want live CSS editing?**
```bash
textual run smart_mirror --dev
```
This enables hot-reload for CSS changes!
