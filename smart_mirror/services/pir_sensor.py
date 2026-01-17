import logging
from typing import Callable
from gpiozero import MotionSensor
from gpiozero.exc import GPIOZeroError

logger = logging.getLogger(__name__)

class PIRSensor:
    """Monitors a PIR sensor and triggers a callback when motion is detected."""

    def __init__(self, pin: int, on_motion: Callable[[], None]):
        """
        Initializes the PIR Sensor.
        Args:
            pin: The GPIO pin number for the PIR sensor.
            on_motion: The callback function to call when motion is detected.
        """
        self.pin = pin
        self.on_motion = on_motion
        self.sensor = None
        try:
            self.sensor = MotionSensor(pin)
            self.sensor.when_motion = self._motion_detected
            logger.info("PIR sensor initialized on pin %d", pin)
        except GPIOZeroError as e:
            logger.error("Failed to initialize PIR sensor on pin %d: %s", pin, e)
            logger.error("Please ensure you are running on a Raspberry Pi and that the gpiozero library is installed and configured correctly.")
        except Exception as e:
            logger.error("An unexpected error occurred during PIR sensor initialization: %s", e)

    def _motion_detected(self):
        """Internal callback for when motion is detected by the sensor."""
        logger.info("Motion detected!")
        if self.on_motion:
            self.on_motion()

    def stop(self):
        """Stops the sensor."""
        if self.sensor:
            self.sensor.close()
            logger.info("PIR sensor stopped.")
