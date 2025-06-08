import adafruit_logging as logging
import gc
import os
from sys import stdout

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.DEBUG)

def log_to_sd():
    # 1. Ensure the /sd/logs/ directory exists
    try:
        # Path to the directory and file
        file_path = "/sd/logs/log.txt"

        # 1. Create the directory if it doesn’t exist
        if "logs" not in os.listdir("/sd"):
            logger.info("Log directory doesn't exist...")
            logger.info("Creating log directory doesn't exist...")
            os.mkdir("/sd/logs")
            logger.info("Log directory created...")
            gc.collect()

        # 2. Create the file if it doesn’t exist
        if "log.txt" not in os.listdir("/sd/logs/"):
            logger.info("Log file doesn't exist...")
            logger.info("Creating log file...")
            with open(file_path, "w"):
                logger.info("Log file created...")
                pass
            gc.collect()
        
        # 3. Start logging to file
        logger.info(f"Attempt to log to file: {file_path}")
        logger.addHandler(logging.FileHandler("/sd/logs/log.txt"))
        
    except Exception as e:
        logger.error(f"Failed to begin logging to file: {e}")