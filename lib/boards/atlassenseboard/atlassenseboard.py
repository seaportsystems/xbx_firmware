import atlas_ezo_do
import atlas_ezo_ec
import atlas_ezo_rtd
import gc

from reading import Reading
from services.global_logger import logger
from services.device_manager import I2CDevice, manager

class EZOEC(I2CDevice):
    def __init__(self, i2c_bus, address=100):
        super().__init__(i2c_bus, address, description="conductivity")

    def initialize_driver(self):
        base_device_driver = atlas_ezo_ec.EZO_EC(i2c_bus=self.i2c_bus, address=self.address)
        return base_device_driver
        
    def deinitialize_device(self):
        try:
            self.base_device.sleep()
            return True
        except Exception as e:
            logger.info(f"Failed to put device to sleep: {e}")
            return False
        
    @property
    def EC(self):
        try:
            return Reading(self.base_device.EC, "uS/cm", "Salinity")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    @property
    def TDS(self):
        try:
            return Reading(self.base_device.TDS, "tds", "Salinity")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    @property
    def S(self):
        try:
            return Reading(self.base_device.S, "S", "Salinity")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    @property
    def SG(self):
        try:
            return Reading(self.base_device.SG, "SG", "Salinity")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['EC'] = self.EC
            
            return readings
        else:
            logger.warning(f"Device is disabled")
            return {}
        
class EZODO(I2CDevice):
    def __init__(self, i2c_bus, address=97):
        super().__init__(i2c_bus, address, description="Dissolved Oxygen")

    def initialize_driver(self):
        base_device_driver = atlas_ezo_do.EZO_DO(i2c_bus=self.i2c_bus, address=self.address)
        return base_device_driver
        
    def deinitialize_device(self):
        try:
            self.base_device.sleep()
            return True
        except Exception as e:
            logger.info(f"Failed to put device to sleep: {e}")
            return False
        
    @property
    def MGL(self):
        try:
            return Reading(self.base_device.MGL, "mg/l", "Dissolved Oxygen")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    @property
    def SAT(self):
        try:
            return Reading(self.base_device.SAT, "%", "Dissolved Oxygen")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['MGL'] = self.MGL
            
            return readings
        else:
            logger.warning(f"Device is disabled")
            return {}

class EZORTD(I2CDevice):
    def __init__(self, i2c_bus, address=102):
        super().__init__(i2c_bus, address, description="Sea Temperature")

    def initialize_driver(self):
        base_device_driver = atlas_ezo_rtd.EZO_RTD(i2c_bus=self.i2c_bus, address=self.address)
        return base_device_driver
        
    def deinitialize_device(self):
        try:
            self.base_device.sleep()
            return True
        except Exception as e:
            logger.info(f"Failed to put device to sleep: {e}")
            return False
        
    @property
    def T(self):
        try:
            return Reading(self.base_device.T, "C", "Sea Temperature")
        
        except Exception as e:
                logger.warning(f"Failed to read {self.description}: {e}")
                self.update_device_status()
                return None
    
    def read(self):
        if self.enabled:
            readings = {}
            
            readings['T'] = self.T
            
            return readings
        else:
            logger.warning(f"Device is disabled")
            return {}
        
class AtlasSenseBoard():
    def __init__(self, parent):
        logger.info("Initializing AtlasSenseBoard")
        
        self.parent = parent
        self.i2c_bus = parent.i2c_bus
        
        logger.info("Adding conductivity sensor to device manager")
        manager.add_device("atlassenseboard.conductivity", EZOEC(self.i2c_bus))
        
        logger.info("Adding dissolved oxygen sensor to device manager")
        manager.add_device("atlassenseboard.dissolvedoxygen", EZODO(self.i2c_bus))
        
        logger.info("Adding watertemperature sensor to device manager")
        manager.add_device("atlassenseboard.watertemperature", EZORTD(self.i2c_bus))
            
        logger.info("Successfully initialized AtlasSenseBoard")
        gc.collect()