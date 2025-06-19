from services.global_logger import logger

# ---- Device Types ---- #
SYSTEM_DEVICE = 0
SENSOR = 1
OTHER = 2

class Device():
    def __init__(self):
        pass
    
    def read(self):
        raise NotImplementedError("Subclasses must implement .read()")
    
class I2CDevice():
    def __init__(self, i2c_bus, address, description):
        self.i2c_bus = i2c_bus
        self.address = address
        self.description = description
        self.enabled = False
        self.base_device = None
        
    @property
    def detected(self):
        locked = False
        while not locked:
            locked = self.i2c_bus.try_lock()
        detected_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if self.address in detected_devices:
            logger.info(f"{self.description} detected on I2C Bus")
            return True
        else:
            logger.info(f"{self.description} not detected on I2C Bus")
            return False
    
    def update_device_status(self):
        logger.info(f"Checking {self.description} status")
        if(not self.detected):
            logger.info(f"Disabling {self.description}")
            self.enabled = False
            self.base_device = None
        else:
            logger.info(f"Enabling {self.description}")
            self.enable()
            
    def enable(self):
        logger.info(f"Enabling {self.description}")
        try:
            if(self.detected):
                self.base_device = self.initialize_driver()
                    
                if self.base_device:
                    logger.info(f"Successfully enabled {self.description}")
                    self.enabled = True
                else:
                    logger.warning(f"Failed to enable {self.description}: base device driver is None")
                    self.enabled = False
                    
            else:
                logger.warning(f"Failed to enable {self.description}: device not found on the bus")
                self.base_device = None
                self.enabled = False
            
        except Exception as e:
            logger.warning(f"Failed to enable {self.description}: {e}")
            self.base_device = None
            self.enabled = False
    
    def disable(self):
        logger.info(f"Disabling {self.description}")
        try:
            if(self.detected):
                deinitialized = self.deinitialize_device()
                    
                if deinitialized:
                    logger.info(f"Successfully deinitialized {self.description}")
                    self.base_device = None
                    self.enabled = False
                else:
                    logger.warning(f"Failed to disable {self.description}")
                    
            else:
                logger.warning(f"Failed to disable {self.description}: device not found on the bus")
                self.base_device = None
                self.enabled = False
            
        except Exception as e:
            logger.warning(f"Failed to enable {self.description}: {e}")
            self.base_device = None
            self.enabled = False

class UARTDevice():
    def __init__(self, uart_bus, description):
        self.uart_bus = uart_bus
        self.description = description
        self.enabled = False
        self.base_device = None
    
    def read(self):
        raise NotImplementedError("Subclasses must implement .read()")
    
    def enable(self):
        logger.info(f"Enabling {self.description}")
        try:
            self.base_device = self.initialize_driver()
                
            if self.base_device:
                logger.info(f"Successfully enabled {self.description}")
                self.enabled = True
            else:
                logger.warning(f"Failed to enable {self.description}: base device driver is None")
                self.enabled = False
            
        except Exception as e:
            logger.warning(f"Failed to enable {self.description}: {e}")
            self.base_device = None
            self.enabled = False
    
    def disable(self):
        logger.info(f"Disabling {self.description}")
        
        try:
            deinitialized = self.deinitialize_device()
                
            if deinitialized:
                logger.info(f"Successfully deinitialized {self.description}")
                self.base_device = None
                self.enabled = False
            else:
                logger.warning(f"Failed to disable {self.description}")       
            
        except Exception as e:
            logger.warning(f"Failed to enable {self.description}: {e}")
            self.base_device = None
            self.enabled = False
            
class DeviceManager():
    def __init__(self):
        self.devices = {}
        
    def all_devices(self):
        """Return a dictionary of all registered device objects."""
        return self.devices

    def all_device_ids(self):
        """Return a list of all registered device IDs."""
        return list(self.devices.keys())
    
    def add_device(self, id, new_device, enable=True):
        # add device to device manager
        # if enable, attempt to enable the device
        self.devices[id] = new_device
        
        if(enable):
            self.devices[id].enable()
            
manager = DeviceManager()