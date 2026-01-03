"""Command-line interface for Smart Mirror TUI."""

from smart_mirror.core.app import SmartMirrorApp


def main():
    """Main CLI entry point."""
    app = SmartMirrorApp()
    app.run()


if __name__ == "__main__":
    main()
