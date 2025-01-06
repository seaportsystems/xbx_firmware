import adafruit_logging as logging
import board
import busio
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

# Initialize SPI Bus
try:
    logger.info("Initializing SPI Bus")
    spi_bus = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
    logger.info("Successfully initialized SPI Bus")

except Exception as e:
    spi_bus = None
    logger.error(f"Failed to initialize SPI Bus: {e}")

# Initialize I2C Bus
try:
    logger.info("Initializing I2C Bus")
    i2c_bus = busio.I2C(scl=board.GP13, sda=board.GP12)
    logger.info("Successfully initialized I2C Bus")

except Exception as e:
    i2c_bus = None
    logger.error(f"Failed to initialize I2C Bus: {e}")

# Initialize UART Bus
try:
    logger.info("Initializing UART Bus")
    uart_bus = busio.UART(tx=board.GP0, rx=board.GP1, baudrate=115200, timeout=10)
    logger.info("Successfully initialized UART Bus")

except:
    i2c_bus = None
    logger.error(f"Failed to initialize UART Bus: {e}")