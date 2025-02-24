import adafruit_logging as logging
import sys
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

from boards.logicboard.logicboard import LogicBoard
from boards.powerboard.powerboard import PowerBoard
from boards.attitudeboard.attitudeboard import AttitudeBoard

# Module Initialization
logicboard = LogicBoard()
powerboard = PowerBoard(logicboard)
attitudeboard = AttitudeBoard(logicboard)