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

print("Creating MQTT Connection")
mqtt_socket = modem.create_mqtt_connection(getenv("DEVICE_ID"), getenv("AWS_IOT_ENDPOINT"))

while True:
    print("")
    print("Modem Status")
    print("------------")
    print(f"Modem Serial Connected: {modem.is_responsive()}")
    print(f"Modem Registered with Network: {modem.is_registered_to_network()}")
    print(f"Modem Packet Data Service Connected: {modem.is_pds_connected()}")
    print(f"Modem Packet Data Protocol Connected: {modem.is_pdp_connected()}")
    print(f"MQTT Socket Open: {mqtt_socket.is_open()}")
    print(f"MQTT Connected: {mqtt_socket.is_connected()}")
    print(f"Modem Comms Ready: {modem.is_comms_ready()}")
    
    if(modem.is_comms_ready()):
        if(not mqtt_socket.is_open()):
            try:
                print("Attempting to open MQTT Connection")
                mqtt_socket.open()
            except ConnectionError as exception:
                print("Failed to open MQTT socket")
        
        if(not mqtt_socket.is_connected()):
            try:
                print("Attempting to establish MQTT Connection")
                mqtt_socket.connect()
            except:
                print("Failed to connect...")
                
        if(mqtt_socket.is_connected()):
            try:
                print(f"Attempting to publish message to: XBX/{getenv('DEVICE_ID')}/device")
                mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/device", "Connected!")
            except Exception as e:
                print(f"Failed to publish: {e}")
    
    time.sleep(1)