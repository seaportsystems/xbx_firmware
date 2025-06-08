import os
import time
from re import sub
from services.global_logger import logger
from gc import collect

logger.info("Initializing data logger")

class DataLogger:
    """
    A minimal data logger that accepts Reading objects and writes them
    to per-description high-resolution CSV files under hrd_dir.
    """

    def __init__(self):
        """
        :param hrd_dir: base directory where high-res CSVs will be written
        """
        
        if "hrd" not in os.listdir("/sd"):
            logger.info("hrd directory doesn't exist...")
            logger.info("Creating hrd directory doesn't exist...")
            os.mkdir("/sd/hrd")
            logger.info("hrd directory created...")
            collect()

    def log_reading(self, reading):
        """
        Append a single Reading to /sd/hrd/{description}.csv.
        Each line will be: "<ISO8601 datetime>,<value>,<unit>\n"

        :param reading: instance of Reading, with attributes:
                        - reading.description (used as filename, with .csv)
                        - reading.datetime   (ISO8601 string)
                        - reading.value      (numeric or str)
                        - reading.unit       (string)
        """
        filename = f"{reading.description}"
        filename = filename.lower()
        filename = filename.strip()
        filename = sub(r'[^a-z0-9]', '', filename)
        filename = f"{filename}.csv"
        filepath = f"/sd/hrd/{filename}"
        
        if filename not in os.listdir("/sd/hrd/"):
            logger.info(f"Data file {filename} doesn't exist...")
            logger.info(f"Creating Data file: {filename}...")
            with open(filepath, "w"):
                logger.info(f"Data file created: {filename}...")
                pass

        line = f"{reading.datetime},{reading.value},{reading.unit}\n"
        try:
            with open(filepath, "a") as f:
                f.write(line)
                f.flush()
        except OSError:
            # If write fails (e.g., no SD card), silently ignore or handle as needed
            pass
    
    collect()