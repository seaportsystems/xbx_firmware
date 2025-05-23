import adafruit_logging as logging
import boards
import json
from os import getenv
from reading import Reading
import services
from sys import stdout
import time
import gc
from random import randint

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)


#--- Open MQTT Connections
modem = boards.logicboard.CellularModem
mqtt_socket = modem.create_mqtt_connection(randint(0,1000), getenv("AWS_IOT_ENDPOINT"))
mqtt_socket.open()
mqtt_socket.connect()

mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "Connected!")
time.sleep(1)
mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "1")
time.sleep(1)
mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "2")
time.sleep(1)
mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "3")
time.sleep(1)
mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "Disconnecting!")
time.sleep(10)
mqtt_socket.disconnect()

while True:
    time.sleep(1)