import adafruit_gps
import adafruit_lps2x
import adafruit_lsm9ds1
import gc
gc.enable()

from reading import Reading
from services.global_logger import logger
from services.device_manager import UARTDevice, I2CDevice, manager

class GPS(UARTDevice):
    def __init__(self, uart_bus):
        super().__init__(uart_bus, description="gps")

    def initialize_driver(self):
        base_device_driver = adafruit_gps.GPS(self.uart_bus)
        return base_device_driver
    
    def deinitialize_device(self):
        return True
        
    @property
    def latlon(self):
        try:
            self.update()
            return Reading(tuple([self.base_device.latitude, self.base_device.longitude]), "degrees", "Location")
        
        except Exception as e:
            logger.warning(f"Failed to read latlon from {self.description}: {e}")
            return None
        
    @property
    def altitude(self):
        try:
            self.update()
            return Reading(self.base_device.altitude_m, "meters", "Altitude")
        
        except Exception as e:
            logger.warning(f"Failed to read altitude from {self.description}: {e}")
            return None
        
    @property
    def hdop(self):
        try:
            self.update()
            return Reading(self.base_device.hdop, "-", "Horizontal Dilution of Precision")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            return None
    
    @property
    def sats(self):
        try:
            self.update()
            return Reading(self.base_device.satellites, "-", "Satellites in View")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            return None
    
    @property
    def fix_quality(self):
        try:
            self.update()
            return Reading(self.base_device.fix_quality, "-", "Fix Quality")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            return None
    
    @property
    def has_fix(self):
        fix_quality = self.fix_quality
        
        if fix_quality.value > 0:
            return True
        else:
            return False
        
    def update(self, updates=10):
        # logger.info(f"Updating GPS data from buffer {updates} times")
        try:
            for _ in range(updates):  # drain a few messages per loop
                self.base_device.update()
                
        except Exception as e:
            logger.warning(f"Failed to update GPS data: {e}")
        
        gc.collect()
        
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['location'] = self.latlon
            readings['altitude'] = self.altitude
            readings['hdop'] = self.hdop
            readings['sv'] = self.sats
            
            gc.collect()
            
            return readings
        
        else:
            logger.warning(f"Device is disabled")
            gc.collect()
            
            return {}
        
class IMU(I2CDevice):
    def __init__(self, i2c_bus, mag_address=28, xg_address=106):
        super().__init__(i2c_bus, address=None, description="imu")
        self.mag_address = mag_address
        self.xg_address = xg_address
        
    @property
    def detected(self):
        locked = False
        while not locked:
            locked = self.i2c_bus.try_lock()
        detected_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        mag_detected = False
        xg_detected = False
        
        if self.mag_address in detected_devices :
            logger.info(f"Magnetometer detected on I2C Bus")
            mag_detected = True
        else:
            logger.warning(f"Magnetometer not detected on I2C Bus")
            
        if self.xg_address in detected_devices :
            logger.info(f"Accelerometer and Gyroscope detected on I2C Bus")
            xg_detected = True
        else:
            logger.warning(f"Acclerometer and Gryoscope not detected on I2C Bus")
            
        if(mag_detected and xg_detected):
            logger.info(f"{self.description} detected on I2C Bus")
            return True
        else:
            logger.warning("IMU not detected on I2C Bus")
            return False
        
    def initialize_driver(self):
        base_device_driver = adafruit_lsm9ds1.LSM9DS1_I2C(self.i2c_bus, mag_address=self.mag_address, xg_address=self.xg_address)
        return base_device_driver
        
    def deinitialize_device(self):
        try:
            # Disable gyroscope (ODR_G = 000 → power-down)
            self.base_device._write_u8(False, 0x10, 0x00)

            # Disable accelerometer (ODR_XL = 000 → power-down)
            self.base_device._write_u8(False, 0x20, 0x00)

            # Disable magnetometer (MD[1:0] = 11 → power-down mode)
            self.base_device._write_u8(True, 0x22, 0x03)
            
            return True
        
        except Exception as e:
            return False
    
    @property
    def accelerations(self):
        try:
            return Reading(tuple(self.base_device.acceleration), "m/s^2", "Acceleration Vector")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
    
    @property
    def rotations(self):
        try:
            return Reading(tuple(self.base_device.gyro), "rad/s", "Angular Velocity")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
    
    @property
    def magnetics(self):
        try:
            return Reading(tuple(self.base_device.magnetic), "uT", "Magnetic Field Vector")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
    
    @property
    def temperature(self):
        try:
            return Reading(self.base_device.temperature, "C", "IMU Temperature")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
    
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['accelerations'] = self.accelerations
            readings['rotations'] = self.rotations
            readings['magnetics'] = self.magnetics
        
            return readings
        else:
            logger.warning(f"Device is disabled")
            return {}
    
class Barometer(I2CDevice):
    def __init__(self, i2c_bus, address=92):
        super().__init__(i2c_bus, address, description="barometer")
        
    def initialize_driver(self):
        base_device_driver = adafruit_lps2x.LPS25(self.i2c_bus, address=self.address)
        return base_device_driver
    
    def deinitialize_device(self):
        try:
            self.base_device.enabled = False
            if(self.base_device.enabled == False):
                return True
            else:
                logger.info(f"Failed to put device to sleep: {e}")
                return False
            
        except Exception as e:
            logger.info(f"Failed to put device to sleep: {e}")
            return False
        
    @property
    def pressure(self):
        try:
            return Reading(self.base_device.pressure, "hPa", "Ambient Pressure")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
        
    @property
    def temperature(self):
        try:
            return Reading(self.base_device.temperature, "C", "Ambient Temperature")
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
    
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['temperature'] = self.temperature
            readings['pressure'] = self.pressure
            
            return readings
        else:
                logger.warning(f"Device is disabled")
                return {}
        
class AttitudeBoard():
    def __init__(self, parent):
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        self.uart_bus = parent.uart_bus_2
        
        logger.info("Adding barometer to device manager")
        manager.add_device("attitudeboard.barometer", Barometer(self.i2c_bus))
        logger.info("Adding imu to device manager")
        manager.add_device("attitudeboard.imu", IMU(self.i2c_bus))
        logger.info("Adding gps to device manager")
        manager.add_device("attitudeboard.gps", GPS(self.uart_bus))
        
        gc.collect()