import adafruit_ds3231
import adafruit_logging as logging
import adafruit_sdcard
import board
import busio
import digitalio
from microcontroller import cpu
import os
import rtc
import storage
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
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
            self.spi_bus = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
            logger.info("Successfully initialized SPI Bus")

        except Exception as e:
            self.spi_bus = None
            logger.error(f"Failed to initialize SPI Bus: {e}")

        # Initialize I2C Bus
        try:
            logger.info("Initializing I2C Bus")
            self.i2c_bus = busio.I2C(scl=board.GP13, sda=board.GP12)
            logger.info("Successfully initialized I2C Bus")

        except Exception as e:
            self.i2c_bus = None
            logger.error(f"Failed to initialize I2C Bus: {e}")

        # Initialize UART Bus
        try:
            logger.info("Initializing UART Bus")
            self.uart_bus = busio.UART(tx=board.GP0, rx=board.GP1, baudrate=115200, timeout=10, receiver_buffer_size=2048)
            logger.info("Successfully initialized UART Bus")

        except:
            self.uart_bus = None
            logger.error(f"Failed to initialize UART Bus: {e}")
            
        # Initialize 2nd UART Bus
        try:
            logger.info("Initializing UART Bus")
            self.uart_bus_2 = busio.UART(tx=board.GP4, rx=board.GP5, baudrate=38400, receiver_buffer_size=2048)
            logger.info("Successfully initialized UART Bus")

        except:
            self.uart_bus_2 = None
            logger.error(f"Failed to initialize UART Bus: {e}")
            
        # Initialize Logicboard Devices
        
        self.cpu = CPU()
        
        # Initialize SD Card
        
        logger.info("Initializing SD Card")
        try:            
            self.sd_card_cs = digitalio.DigitalInOut(board.GP2)
            self.sd_card_cs.direction = digitalio.Direction.OUTPUT
            self.sd_card_cd = digitalio.DigitalInOut(board.GP3)
            self.sd_card_cd.direction = digitalio.Direction.INPUT
            
            if(not(self.sd_card_cd.value)):
                self.sd_card = adafruit_sdcard.SDCard(self.spi_bus, self.sd_card_cs)
                self.vfs = storage.VfsFat(self.sd_card)
                storage.mount(self.vfs, "/sd")
                logger.info("Successfully initialized SD Card")

            else:
                logger.error(f"SD Card not detected: {not(self.sd_card_cd.value)}")
                
        except Exception as e:
            logger.error(f"Failed to initialize SD Card: {e}")
            
        # Initialize RTC
        logger.info("Initializing RTC")
        try:
            self.RTC = RTC(self.i2c_bus)
            logger.info("Successfully initialized RTC")
        except Exception as e:
            logger.info(f"Failed to initialize RTC: {e}")
        
        # Initialize Onboard RTC
        logger.info("Initializing Onboard RTC")
        try:
            self.OnboardRTC = rtc.RTC()
            logger.info("Successfully initialized Onboard RTC")
            self.OnboardRTC.datetime = self.RTC.datetime
            logger.info("Successfully synced Logicboard RTC and Onboard RTC")
        except Exception as e:
            logger.info(f"Failed to initialize Onboard RTC: {e}")