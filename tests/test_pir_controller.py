"""Tests for the PIR screen controller service."""

from unittest.mock import MagicMock, call, patch

import pytest

from smart_mirror.services.pir_controller import PIRScreenController


@pytest.fixture
def mock_sensor():
    """Create a mock motion sensor."""
    sensor = MagicMock()
    sensor.when_motion = None
    return sensor


@pytest.fixture
def controller(mock_sensor):
    """Create a PIRScreenController with a mock sensor factory."""
    factory = MagicMock(return_value=mock_sensor)
    ctrl = PIRScreenController(
        gpio_pin=26,
        screen_output="HDMI-A-1",
        timeout=120,
        motion_sensor_factory=factory,
    )
    return ctrl


def test_start_creates_sensor(controller, mock_sensor):
    """start() creates a sensor on the correct pin and registers the motion callback."""
    controller.start()

    controller._motion_sensor_factory.assert_called_once_with(26)
    assert mock_sensor.when_motion == controller._on_motion


@patch.object(PIRScreenController, "_run_screen_command")
def test_motion_turns_screen_on(mock_cmd, controller, mock_sensor):
    """First motion event turns the screen on."""
    controller.start()
    controller._on_motion()

    mock_cmd.assert_called_once_with("--on")
    assert controller._screen_on is True


@patch.object(PIRScreenController, "_run_screen_command")
def test_motion_does_not_turn_on_twice(mock_cmd, controller, mock_sensor):
    """Repeated motion doesn't issue redundant on commands, but resets the timer."""
    controller.start()
    controller._on_motion()
    controller._on_motion()

    # Screen on command called only once
    mock_cmd.assert_called_once_with("--on")
    # But a timer is still active (reset on second call)
    assert controller._timer is not None


@patch.object(PIRScreenController, "_run_screen_command")
def test_timeout_turns_screen_off(mock_cmd, controller, mock_sensor):
    """When the inactivity timer fires, the screen turns off."""
    controller.start()
    controller._on_motion()

    # Simulate the timer firing
    controller._on_timeout()

    assert mock_cmd.call_args_list == [call("--on"), call("--off")]
    assert controller._screen_on is False
    assert controller._timer is None


@patch("smart_mirror.services.pir_controller.threading.Timer")
@patch.object(PIRScreenController, "_run_screen_command")
def test_motion_resets_timer(mock_cmd, mock_timer_cls, controller, mock_sensor):
    """New motion cancels the existing timer and starts a fresh one."""
    first_mock_timer = MagicMock()
    second_mock_timer = MagicMock()
    mock_timer_cls.side_effect = [first_mock_timer, second_mock_timer]

    controller.start()
    controller._on_motion()
    controller._on_motion()

    first_mock_timer.cancel.assert_called_once()
    second_mock_timer.start.assert_called_once()
    assert controller._timer is second_mock_timer


@patch("smart_mirror.services.pir_controller.threading.Timer")
@patch.object(PIRScreenController, "_run_screen_command")
def test_stop_cleans_up(mock_cmd, mock_timer_cls, controller, mock_sensor):
    """stop() cancels the timer, closes the sensor, and turns screen off."""
    mock_timer = MagicMock()
    mock_timer_cls.return_value = mock_timer

    controller.start()
    controller._on_motion()
    controller.stop()

    mock_timer.cancel.assert_called()
    mock_sensor.close.assert_called_once()
    assert controller._sensor is None
    assert controller._timer is None
    # Screen was on, so --off should have been called
    assert call("--off") in mock_cmd.call_args_list


@patch("smart_mirror.services.pir_controller.subprocess.run")
def test_screen_command_uses_correct_env_and_output(mock_run, controller):
    """_run_screen_command passes the right wlr-randr arguments and Wayland env."""
    controller._run_screen_command("--on")

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["wlr-randr", "--output", "HDMI-A-1", "--on"]
    assert kwargs["env"]["XDG_RUNTIME_DIR"] == "/run/user/1000"
    assert kwargs["env"]["WAYLAND_DISPLAY"] == "wayland-0"
    assert kwargs["check"] is False


def test_stop_when_not_started(controller):
    """Calling stop() before start() doesn't raise."""
    controller.stop()  # Should not raise
