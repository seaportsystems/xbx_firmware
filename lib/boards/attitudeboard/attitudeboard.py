import adafruit_gps
import adafruit_logging as logging
import adafruit_lps2x
import adafruit_lsm9ds1
from sys import stdout
import gc

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)

class GPS():
    def __init__(self, uart_bus):
        self.uart_bus = uart_bus
        self.base_device = adafruit_gps.GPS(self.uart_bus)
        
    @property
    def latlon(self):
        return (self.base_device.latitude_degrees, self.base_device.longitude_degrees)
        
    @property
    def hdop(self):
        return self.base_device.hdop
    
    @property
    def sats(self):
        return self.base_device.satellites
    
    def update(self):
        self.base_device.update()
        
class IMU():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
            
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(28 in i2c_devices):
            mag_address = 28
        elif(30 in i2c_devices):
            mag_address = 30
        else:
            raise RuntimeError("Magnetometer not found on the I2C Bus")
        
        if(106 in i2c_devices):
            xg_address = 106
        elif(107 in i2c_devices):
            xg_address = 107
        else:
            raise RuntimeError("Accelerometer/Gyroscope not found on the I2C Bus")
        
        self.base_device = adafruit_lsm9ds1.LSM9DS1_I2C(self.i2c_bus, mag_address=mag_address, xg_address=xg_address)
        
    @property
    def accelerations(self):
        return tuple(self.base_device.acceleration)
    
    @property
    def rotations(self):
        return tuple(self.base_device.gyro)
    
    @property
    def magnetics(self):
        return tuple(self.base_device.magnetic)
    
    @property
    def temperature(self):
        return self.base_device.temperature
    

class Barometer():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
        
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(92 in i2c_devices):
            address = 92
        elif(93 in i2c_devices):
            address = 93
        else:
            raise RuntimeError("Magnetometer not found on the I2C Bus")
        
        self.base_device = adafruit_lps2x.LPS25(self.i2c_bus, address=address)
        
    @property
    def pressure(self):
        return self.base_device.pressure
        
    @property
    def temperature(self):
        return self.base_device.temperature
        
class AttitudeBoard():
    def __init__(self, parent):
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        self.uart_bus = parent.uart_bus_2
        
        self.imu = IMU(self.i2c_bus)
        self.barometer = Barometer(self.i2c_bus)
        self.gps = GPS(self.uart_bus)
        gc.collect()