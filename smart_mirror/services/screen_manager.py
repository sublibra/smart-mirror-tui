import logging
import subprocess

logger = logging.getLogger(__name__)

class ScreenManager:
    """Manages the screen state, turning it on and off as required."""

    def __init__(self, output_name: str = "HDMI-A-1"):
        """
        Initializes the ScreenManager.
        Args:
            output_name: The name of the display output (e.g., HDMI-A-1).
        """
        self.output_name = output_name

    def _run_command(self, command: str) -> None:
        """
        Executes a shell command.
        Args:
            command: The command to execute.
        """
        try:
            logger.info("Executing screen command: %s", command)
            subprocess.Popen(command, shell=True)
        except Exception as e:
            logger.error("Error executing screen command: %s", e)

    def screen_on(self) -> None:
        """Turns the screen on."""
        command = f'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlr-randr --output {self.output_name} --on'
        self._run_command(command)

    def screen_off(self) -> None:
        """Turns the screen off."""
        command = f'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlr-randr --output {self.output_name} --off'
        self._run_command(command)
