# import adafruit_gps
import adafruit_lps2x
import adafruit_lsm9ds1
import gc
gc.enable()

from reading import Reading
from services.global_logger import logger
from services.device_manager import I2CDevice, manager

# class GPS():
#     def __init__(self, uart_bus):
#         self.uart_bus = uart_bus
#         self.base_device = adafruit_gps.GPS(self.uart_bus)
        
#     @property
#     def latlon(self):
#         return (self.base_device.latitude_degrees, self.base_device.longitude_degrees)
        
#     @property
#     def hdop(self):
#         return self.base_device.hdop
    
#     @property
#     def sats(self):
#         return self.base_device.satellites
    
#     def update(self):
#         self.base_device.update()
        
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
        readings = {}
        
        readings['accelerations'] = self.accelerations
        readings['rotations'] = self.rotations
        readings['magnetics'] = self.magnetics
        
        return readings
    
class Barometer(I2CDevice):
    def __init__(self, i2c_bus, address=92):
        super().__init__(i2c_bus, address, description="barometer")
        
    def initialize_driver(self):
        base_device_driver = adafruit_lps2x.LPS25(self.i2c_bus, address=self.address)
        return base_device_driver
    
    @property
    def pressure(self):
        try:
            return Reading(self.base_device.pressure, "hPa", "Pressure")
        
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
        readings = {}
        
        readings['temperature'] = self.temperature
        readings['pressure'] = self.pressure
        
        return readings
        
class AttitudeBoard():
    def __init__(self, parent):
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        self.uart_bus = parent.uart_bus_2
        
        logger.info("Adding barometer to device manager")
        manager.add_device("attitudeboard.barometer", Barometer(self.i2c_bus))
        logger.info("Adding imu to device manager")
        manager.add_device("attitudeboard.imu", IMU(self.i2c_bus))

        # self.gps = GPS(self.uart_bus)
        gc.collect()