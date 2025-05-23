import bg95m3
import boards
import adafruit_logging as logging
import sys
import os
from time import sleep

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

modem = boards.logicboard.CellularModem

while True:
    print(modem.get_signal_quality())
    sleep(1)