"""PIR sensor screen controller for the smart mirror."""

import os
import subprocess
import threading
from typing import Callable, Optional


class PIRScreenController:
    """Controls screen power based on PIR motion sensor input.

    Turns the screen on when motion is detected and off after a configurable
    timeout of inactivity. Uses wlr-randr for Wayland display control.

    Args:
        gpio_pin: GPIO pin number for the PIR sensor (default 26).
        screen_output: wlr-randr output name (default "HDMI-A-1").
        timeout: Seconds of inactivity before screen turns off (default 120).
        motion_sensor_factory: Callable that creates a motion sensor given a pin.
            Defaults to gpiozero.MotionSensor. Override for testing.
    """

    def __init__(
        self,
        gpio_pin: int = 26,
        screen_output: str = "HDMI-A-1",
        timeout: int = 120,
        motion_sensor_factory: Optional[Callable] = None,
    ):
        self._gpio_pin = gpio_pin
        self._screen_output = screen_output
        self._timeout = timeout
        self._motion_sensor_factory = motion_sensor_factory or self._default_sensor_factory
        self._sensor = None
        self._timer: Optional[threading.Timer] = None
        self._screen_on = False
        self._lock = threading.Lock()

    @staticmethod
    def _default_sensor_factory(pin: int):
        from gpiozero import MotionSensor

        return MotionSensor(pin)

    def start(self) -> None:
        """Create the motion sensor and begin listening for motion events."""
        self._sensor = self._motion_sensor_factory(self._gpio_pin)
        self._sensor.when_motion = self._on_motion

    def stop(self) -> None:
        """Stop listening, cancel pending timer, close sensor, turn screen off."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if self._sensor is not None:
                self._sensor.close()
                self._sensor = None
            self._turn_screen_off()

    def _on_motion(self) -> None:
        """Handle motion detected: turn screen on and reset the inactivity timer."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._turn_screen_on()
            self._timer = threading.Timer(self._timeout, self._on_timeout)
            self._timer.daemon = True
            self._timer.start()

    def _on_timeout(self) -> None:
        """Handle inactivity timeout: turn screen off."""
        with self._lock:
            self._timer = None
            self._turn_screen_off()

    def _turn_screen_on(self) -> None:
        if not self._screen_on:
            self._run_screen_command("--on")
            self._screen_on = True

    def _turn_screen_off(self) -> None:
        if self._screen_on:
            self._run_screen_command("--off")
            self._screen_on = False

    def _run_screen_command(self, flag: str) -> None:
        """Execute wlr-randr to control the screen output."""
        env = {
            **os.environ,
            "XDG_RUNTIME_DIR": "/run/user/1000",
            "WAYLAND_DISPLAY": "wayland-0",
        }
        subprocess.run(
            ["wlr-randr", "--output", self._screen_output, flag],
            env=env,
            check=False,
        )
