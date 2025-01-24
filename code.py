import adafruit_logging as logging
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

logger.info("Initializing...")
import board
import json
import os
import random
import sdcardio
import storage
import time

# Start logging to file
try:
    logger.addHandler(logging.FileHandler(f'sd/{__name__}.log', 'a'))
    logger.info(f"Logging to /sd/{__name__}.log")
except Exception as e:
    logger.warning(f"Failed to add FileHandler to logger: {e}")

import xbx_busses
import xbx_devices

import seaport_systems_bg95m3 as bg95m3

modem = bg95m3.BG95M3(xbx_busses.uart_bus)

s = modem.create_mqtt_connection(f"xbx_devkit_{random.randint(0,99)}", "a2jgs36qfd35dk-ats.iot.us-east-2.amazonaws.com", port=8883)
print("Openning Socket")
s.open()
print("Connecting to MQTT Broker")
s.connect()

s.publish(1, 1, "xbx_devkit/log", "Hello from XBX")
time.sleep(1)
s.publish(1, 1, "xbx_devkit/log", "Hello from XBX")
time.sleep(1)
s.publish(1, 1, "xbx_devkit/log", "Hello from XBX")
s.publish(1, 1, "xbx_devkit/log", "Disconnecting now...")

s.disconnect()
s.close()