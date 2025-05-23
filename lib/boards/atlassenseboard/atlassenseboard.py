import adafruit_logging as logging
import atlas_ezo_do
import atlas_ezo_ec
import atlas_ezo_rtd
from sys import stdout
import gc

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)
        
class EZOEC():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
            
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(100 in i2c_devices):
            address = 100
        else:
            raise RuntimeError("EZOEC not found on the I2C Bus")
        
        self.base_device = atlas_ezo_ec.EZO_EC(i2c_bus=self.i2c_bus, address=address)
        
    @property
    def EC(self):
        return self.base_device.EC
    
    @property
    def TDS(self):
        return self.base_device.TDS
    
    @property
    def S(self):
        return self.base_device.S
    
    @property
    def SG(self):
        return self.base_device.SG
        
class EZODO():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
            
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(97 in i2c_devices):
            address = 97
        else:
            raise RuntimeError("EZODO not found on the I2C Bus")
        
        self.base_device = atlas_ezo_do.EZO_DO(i2c_bus=self.i2c_bus, address=address)
        
    @property
    def MGL(self):
        return self.base_device.MGL
    
    @property
    def SAT(self):
        return self.base_device.SAT

class EZORTD():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
            
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(102 in i2c_devices):
            address = 102
        else:
            raise RuntimeError("EZODO not found on the I2C Bus")
        
        self.base_device = atlas_ezo_rtd.EZO_RTD(i2c_bus=self.i2c_bus, address=address)
        
    @property
    def T(self):
        return self.base_device.T
        
class AtlasSenseBoard():
    def __init__(self, parent):
        logger.info("Initializing AtlasSenseBoard")
        
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        
        logger.info("Initializing EZOEC")
        try:
            self.EZO_EC = EZOEC(self.i2c_bus)
            logger.info("Successfully initialized EZOEC")
        except Exception as e:
            logger.warning(f"Failed to initialize EZOEC: {e}")
        
        logger.info("Initializing EZODO")
        try:
            self.EZO_DO = EZODO(self.i2c_bus)
            logger.info("Successfully initialized EZODO")
        except Exception as e:
            logger.warning(f"Failed to initialize EZODO: {e}")
        
        logger.info("Initializing EZORTD")
        try:
            self.EZO_RTD = EZORTD(self.i2c_bus)
            logger.info("Successfully initialized EZORTD")
        except Exception as e:
            logger.warning(f"Failed to initialize EZORTD: {e}")
            
    logger.info("Successfully initialized AtlasSenseBoard")
    gc.collect()