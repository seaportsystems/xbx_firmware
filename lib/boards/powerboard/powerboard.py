import adafruit_logging as logging
import adafruit_max1704x
from sys import stdout
import gc

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)

class BatteryMonitor():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
        
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(54 in i2c_devices):
            address = 54
            try:
                self.base_device = adafruit_max1704x.MAX17048(self.i2c_bus, address=address)
                self.initialized = True
            except:
                self.base_device = None
                self.initialized = False
        else:
            logger.error("Battery Monitor not found on the I2C Bus")
            self.base_device = None
            self.initialized = False
        
    @property
    def percent(self):
        return self.base_device.cell_percent
        
    @property
    def voltage(self):
        return self.base_device.cell_voltage
        
    @property
    def charge_rate(self):
        return self.base_device.charge_rate
    
class PowerBoard():
    def __init__(self, parent):
        logger.info("Initializing Powerboard")
        
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        
        logger.info("Initializing Battery Monitor")
        
        try:
            self.battery_monitor = BatteryMonitor(self.i2c_bus)
            logger.info("Successfully initialized Battery Monitor")
            
        except Exception as e:
            logger.error(f"Failed to initialize Battery Monitor: {e}")
            
        gc.collect()