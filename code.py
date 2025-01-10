
import adafruit_logging as logging
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

logger.info("Initializing...")
import board
import json
import os
import sdcardio
import storage
import time

import xbx_busses

# Initialize SD Card
try:
    logger.info("Initializing SD Card")
    sd_card = sdcardio.SDCard(xbx_busses.spi_bus, board.GP28)
    vfs = storage.VfsFat(sd_card)
    storage.mount(vfs, '/sd')
    logger.info("Successfully initialized SD Card")

except Exception as e:
    logger.error(f"Failed to initialize SD Card: {e}")

# Start logging to file
try:
    logger.addHandler(logging.FileHandler(f'sd/{__name__}.log', 'a'))
    logger.info(f"Logging to /sd/{__name__}.log")
except Exception as e:
    logger.warning(f"Failed to add FileHandler to logger: {e}")

import xbx_devices
import xbx_comms

# Main Loop
while True:
    for sensor in xbx_devices.initialized_sensors:
        measurement = sensor.get_measurement()
        measurement_json = json.dumps(measurement.__dict__)
        xbx_comms.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/{sensor.topic}", msg=measurement_json)
        logger.info(f"Published message to XBX/{os.getenv('DEVICE_ID')}/readings/{sensor.topic}: {measurement_json}")

    time.sleep(1)