import adafruit_ds3231
import bg95m3
import adafruit_logging as logging
from adafruit_sdcard import SDCard
import board
from busio import SPI, I2C, UART
from digitalio import DigitalInOut, Direction
from microcontroller import cpu
import rtc
from storage import VfsFat, mount
from sys import stdout
import gc

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)

class CPU():
    def __init__(self):
        self.base_device = cpu
        
    @property
    def temperature(self):
        return self.base_device.temperature
    
class RTC():
    def __init__(self, i2c_bus):
        self.i2c_bus = i2c_bus
        
        locked = False
        while(not(locked)):
            locked = self.i2c_bus.try_lock()
        i2c_devices = self.i2c_bus.scan()
        self.i2c_bus.unlock()
        
        if(104 in i2c_devices):
            address = 104
        else:
            raise RuntimeError("Battery Monitor not found on the I2C Bus")
        
        self.base_device = adafruit_ds3231.DS3231(i2c_bus)
        
        if(self.base_device.lost_power):
            logger.info("RTC has lost power since the time was last set")
    
    @property
    def datetime(self):
        return self.base_device.datetime
    
    @datetime.setter
    def datetime(self, new_time):
        self.base_device.datetime = new_time
    
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
        
        # # Initialize Cellular Modem
        # logger.info("Initializing Cellular Modem")
        # try:
        #     self.CellularModem = bg95m3.BG95M3(self.uart_bus)
        #     logger.info("Successfully initialized Cellular Modem")
        # except Exception as e:
        #     logger.info(f"Failed to initialize Cellular Modem: {e}")
            
        # Initialize RTC
        logger.info("Initializing RTC")
        try:
            self.rtc = RTC(self.i2c_bus)
            logger.info("Successfully initialized RTC")
        except Exception as e:
            logger.info(f"Failed to initialize RTC: {e}")
        
        # Initialize Onboard RTC
        logger.info("Initializing Onboard RTC")
        try:
            self.OnboardRTC = rtc.RTC()
            logger.info("Successfully initialized Onboard RTC")
            self.OnboardRTC.datetime = self.rtc.datetime
            logger.info("Successfully synced Logicboard RTC and Onboard RTC")
        except Exception as e:
            logger.info(f"Failed to initialize Onboard RTC: {e}")
    
    gc.collect()