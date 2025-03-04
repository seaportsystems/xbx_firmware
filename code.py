import adafruit_logging as logging
import boards
import json
import os
from reading import Reading
import services
import sys
import time

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

while True:
    
    accelerations = Reading(boards.attitudeboard.imu.accelerations, "m/s^2", "Acceleration Vector")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/acceleration", msg=json.dumps(accelerations.__dict__))
    
    rotations = Reading(boards.attitudeboard.imu.rotations, "rad/s", "Angular Velocity")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/angular_velocity", msg=json.dumps(rotations.__dict__))
    
    magnetics = Reading(boards.attitudeboard.imu.magnetics, "uT", "Magnetic Field Vector")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/magnetics", msg=json.dumps(magnetics.__dict__))
    
    pressure = Reading(boards.attitudeboard.barometer.pressure, "hPa", "Pressure")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/pressure", msg=json.dumps(pressure.__dict__))
    
    ambient_temperature = Reading(boards.attitudeboard.barometer.temperature, "C", "Ambient Temperature")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/ambient_temperature", msg=json.dumps(ambient_temperature.__dict__))
    
    cpu_temperature = Reading(boards.logicboard.cpu.temperature, "C", "CPU Temperature")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/cpu_temperature", msg=json.dumps(cpu_temperature.__dict__))

    latlon = Reading(boards.attitudeboard.gps.latlon, "degrees", "Location")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/location", msg=json.dumps(latlon.__dict__))
    
    hdop = Reading(boards.attitudeboard.gps.hdop, "degrees", "Horizontal Dilution of Precision")
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/hdop", msg=json.dumps(hdop.__dict__))
    
    satellites = Reading(boards.attitudeboard.gps.latlon, "-", "Satellites in View") 
    services.mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/readings/satellites", msg=json.dumps(satellites.__dict__))
    
    time.sleep(1)