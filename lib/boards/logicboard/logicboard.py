import adafruit_ds3231
from bg95m3 import BG95M3
from adafruit_sdcard import SDCard
import board
from busio import SPI, I2C, UART
from digitalio import DigitalInOut, Direction
from microcontroller import cpu
import rtc
from storage import VfsFat, mount
import gc
gc.enable()

from reading import Reading
from services.global_logger import logger, log_to_sd
from services.device_manager import Device, I2CDevice, manager

class CPU(Device):
    def __init__(self):
        self.base_device = cpu
        self.description = "cpu"
        
    @property
    def temperature(self):
        try:
            return self.base_device.temperature
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            return None

    def read(self):
        readings = {}
        
        readings['cpu_temperature'] = self.temperature
        
        return readings
    
class RTC(I2CDevice):
    def __init__(self, i2c_bus, address=104):
        super().__init__(i2c_bus, address, description="real time clock")

    def initialize_driver(self):
        base_device_driver = adafruit_ds3231.DS3231(self.i2c_bus)
        return base_device_driver
    
    @property
    def datetime(self):
        try:
            return self.base_device.datetime
        
        except Exception as e:
            logger.warning(f"Failed to read {self.description}: {e}")
            self.update_device_status()
            return None
        
    @datetime.setter
    def datetime(self, new_time):
        self.base_device.datetime = new_time
        
    def read(self):
        readings = {}
        
        readings['datetime'] = self.datetime
        
        return readings
    
class LogicBoard():
    def __init__(self):
        logger.info("Initializing Logicboard")
        # Initialize all communication busses
        # Initialize SPI Bus
        try:
            logger.info("Initializing SPI Bus")
            self.spi_bus = SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
            logger.info("Successfully initialized SPI Bus")

        except Exception as e:
            self.spi_bus = None
            logger.error(f"Failed to initialize SPI Bus: {e}")

        # Initialize I2C Bus
        try:
            logger.info("Initializing I2C Bus")
            self.i2c_bus = I2C(scl=board.GP13, sda=board.GP12)
            logger.info("Successfully initialized I2C Bus")

        except Exception as e:
            self.i2c_bus = None
            logger.error(f"Failed to initialize I2C Bus: {e}")

        # Initialize UART Bus
        try:
            logger.info("Initializing UART Bus")
            self.uart_bus = UART(tx=board.GP0, rx=board.GP1, baudrate=115200, timeout=10, receiver_buffer_size=2048)
            logger.info("Successfully initialized UART Bus")

        except:
            self.uart_bus = None
            logger.error(f"Failed to initialize UART Bus: {e}")
            
        # Initialize 2nd UART Bus
        try:
            logger.info("Initializing UART Bus")
            self.uart_bus_2 = UART(tx=board.GP4, rx=board.GP5, baudrate=38400, receiver_buffer_size=2048)
            logger.info("Successfully initialized UART Bus")

        except:
            self.uart_bus_2 = None
            logger.error(f"Failed to initialize UART Bus: {e}")
            
        # Initialize Logicboard Devices
        
        self.cpu = CPU()
        
        # Initialize SD Card
        
        logger.info("Initializing SD Card")
        try:            
            self.sd_card_cs = DigitalInOut(board.GP2)
            self.sd_card_cs.direction = Direction.OUTPUT
            self.sd_card_cd = DigitalInOut(board.GP3)
            self.sd_card_cd.direction = Direction.INPUT
            
            if(not(self.sd_card_cd.value)):
                self.sd_card = SDCard(self.spi_bus, self.sd_card_cs)
                self.vfs = VfsFat(self.sd_card)
                mount(self.vfs, "/sd")
                logger.info("Successfully initialized SD Card")

            else:
                logger.error(f"SD Card not detected: {not(self.sd_card_cd.value)}")
                
        except Exception as e:
            logger.error(f"Failed to initialize SD Card: {e}")
        logger.info("Beginning log to SD Card")
        
        log_to_sd()
        
        # Initialize Cellular Modem
        logger.info("Initializing Cellular Modem")
        try:
            self.CellularModem = BG95M3(self.uart_bus)
            logger.info("Successfully initialized Cellular Modem")
        except Exception as e:
            logger.info(f"Failed to initialize Cellular Modem: {e}")
            
        # Initialize RTC
        logger.info("Adding RTC to device manager")
        manager.add_device('logicboard.rtc', RTC(self.i2c_bus))
        
        # Initialize Onboard RTC
        logger.info("Initializing Onboard RTC")
        try:
            self.OnboardRTC = rtc.RTC()
            logger.info("Successfully initialized Onboard RTC")
            self.OnboardRTC.datetime = manager.devices['logicboard.rtc'].datetime
            
            logger.info("Successfully synced Logicboard RTC and Onboard RTC")
        except Exception as e:
            logger.info(f"Failed to initialize Onboard RTC: {e}")
    
    gc.collect()
    
