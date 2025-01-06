import adafruit_logging as logging
import board
import sdcardio
import storage
import sys

import xbx_busses
import xbx_sensor_config

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

# Start logging to file
try:
    logger.addHandler(logging.FileHandler(f'sd/{__name__}.log', 'a'))
    logger.info(f"Logging to /sd/{__name__}.log")
except Exception as e:
    logger.warning(f"Failed to add FileHandler to logger: {e}")

logger.setLevel(logging.DEBUG)

# Initialize Sensors
initialized_sensors = []

def initialize_sensor(sensor_class):
    try:
        logger.info(f"Initializing {sensor_class}")
        initialized_sensors.append(sensor_class())
        logger.info(f"Successfully initialized {sensor_class}")
    except Exception as e:
        logger.error(f"Failed to initialize {sensor_class}: {e}")

initialize_sensor(xbx_sensor_config.RP2040T)
initialize_sensor(xbx_sensor_config.LSM303AGR)
initialize_sensor(xbx_sensor_config.LIS2MDL)
initialize_sensor(xbx_sensor_config.EZODO)
initialize_sensor(xbx_sensor_config.EZOEC)