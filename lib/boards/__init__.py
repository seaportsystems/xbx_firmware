import adafruit_logging as logging
from sys import stdout

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)

from boards.logicboard.logicboard import LogicBoard
from boards.powerboard.powerboard import PowerBoard
from boards.attitudeboard.attitudeboard import AttitudeBoard
from boards.atlassenseboard.atlassenseboard import AtlasSenseBoard

# Module Initialization
logicboard = LogicBoard()
# powerboard = PowerBoard(logicboard)
# attitudeboard = AttitudeBoard(logicboard)
# atlassenseboard = AtlasSenseBoard(logicboard)