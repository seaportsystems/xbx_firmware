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
time.sleep(5)
mqtt_socket.connect()

mqtt_socket.publish(1, 0, f"XBX/{getenv('DEVICE_ID')}/device", "Connected!")
time.sleep(1)

while True:    
    accelerations = Reading(boards.attitudeboard.imu.accelerations, "m/s^2", "Acceleration Vector")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/acceleration", json.dumps(accelerations.__dict__))
    
    rotations = Reading(boards.attitudeboard.imu.rotations, "rad/s", "Angular Velocity")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/angular_velocity", json.dumps(rotations.__dict__))
    
    magnetics = Reading(boards.attitudeboard.imu.magnetics, "uT", "Magnetic Field Vector")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/magnetics", json.dumps(magnetics.__dict__))
    
    pressure = Reading(boards.attitudeboard.barometer.pressure, "hPa", "Pressure")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/pressure", json.dumps(pressure.__dict__))

    salinity = Reading(boards.atlassenseboard.EZOEC.EC, "uS/cm", "Salinity") 
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/salinity", json.dumps(salinity.__dict__))
    
    dissolved_oxygen = Reading(boards.atlassenseboard.EZODO.MGL, "mg/l", "Dissolved Oxygen") 
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/dissolved_oxygen", json.dumps(dissolved_oxygen.__dict__))
    
    water_temperature = Reading(boards.atlassenseboard.EZORTD.T, "C", "Water Temperature") 
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/water_temperature", json.dumps(water_temperature.__dict__))
    
    ambient_temperature = Reading(boards.attitudeboard.barometer.temperature, "C", "Ambient Temperature")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/ambient_temperature", json.dumps(ambient_temperature.__dict__))
    
    cpu_temperature = Reading(boards.logicboard.cpu.temperature, "C", "CPU Temperature")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/cpu_temperature", json.dumps(cpu_temperature.__dict__))

    latlon = Reading(boards.attitudeboard.gps.latlon, "degrees", "Location")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/location", json.dumps(latlon.__dict__))
    
    hdop = Reading(boards.attitudeboard.gps.hdop, "degrees", "Horizontal Dilution of Precision")
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/hdop", json.dumps(hdop.__dict__))
    
    satellites = Reading(boards.attitudeboard.gps.latlon, "-", "Satellites in View") 
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/readings/satellites", json.dumps(satellites.__dict__))
    
    mqtt_socket.publish(f"XBX/{getenv('DEVICE_ID')}/device", "Sleeping until next set of readings")
    time.sleep(1)