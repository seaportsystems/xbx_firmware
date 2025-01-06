import adafruit_logging as logging
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
# Start logging to file
try:
    logger.addHandler(logging.FileHandler(f'sd/{__name__}.log', 'a'))
    logger.info("Logging to /sd/{__name__}.log")
except Exception as e:
    logger.warning(f"Failed to add FileHandler to logger: {e}")
logger.setLevel(logging.DEBUG)

import xbx_busses

from sensor import Sensor
from reading import Reading

class RP2040T(Sensor):
    def __repr__(self):
        return "RP2040 CPU Temperature Sensor"
    
    def __init__(self, topic="tem"):
        super().__init__(topic)

        from microcontroller import cpu
        self.base_device = cpu

    def get_measurement(self):
        try:
            return Reading(self.base_device.temperature, "C", "CPU Temperature")
        except Exception as e:
            logger.warning(f"Failed to get measurement: {e}")
            return Reading(None, "C", "CPU Temperature")
    
class LSM303AGR(Sensor):
    def __repr__(self):
        return "LSM303AGR Accelerometer"
    
    def __init__(self, topic="acc"):
        super().__init__(topic)

        from adafruit_lsm303_accel import LSM303_Accel

        self.base_device = LSM303_Accel(xbx_busses.i2c_bus)

    def get_measurement(self):
        try:
            return Reading(self.base_device.acceleration, "G", "Accelerations")
        except Exception as e:
            logger.warning(f"Failed to get measurement: {e}")
            return Reading(None, "G", "Accelerations")
        
class LIS2MDL(Sensor):
    def __repr__(self):
        return "LIS2MDL Magnetometer"
    
    def __init__(self, topic="mag"):
        super().__init__(topic)

        from adafruit_lis2mdl import LIS2MDL as LIS2MDL_Mag
    
        self.base_device = LIS2MDL_Mag(xbx_busses.i2c_bus)

    def get_measurement(self):
        try:
            return Reading(self.base_device.magnetic, "T", "Magnetics")
        except Exception as e:
            logger.warning(f"Failed to get measurement: {e}")
            return Reading(None, "T", "Magnetics")

class EZOEC(Sensor):
    def __repr__(self):
        return "EZO Electrical Conductivity Sensor"
    
    def __init__(self, topic="ecc"):
        super().__init__(topic)

        from atlas_ezo_ec import EZO_EC
        
        self.base_device = EZO_EC(xbx_busses.i2c_bus)

    def get_measurement(self):
        try:
            return Reading(self.base_device.S, "us/cm", "Salinity")
        except Exception as e:
            logger.warning(f"Failed to get measurement: {e}")
            return Reading(None, "us/cm", "Salinity")
        
class EZODO(Sensor):
    def __repr__(self):
        return "EZO Dissolved Oxygen Sensor"
    
    def __init__(self, topic="dox"):
        super().__init__(topic)

        from atlas_ezo_do import EZO_DO
        
        self.base_device = EZO_DO(xbx_busses.i2c_bus)
    
    def get_measurement(self):
        try:
            return Reading(self.base_device.MGL, "mg/L", "Dissolved Oxygen")
        except Exception as e:
            logger.warning(f"Failed to get measurement: {e}")
            return Reading(None, "mg/L", "Dissolved Oxygen")