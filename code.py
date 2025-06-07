import adafruit_logging as logging
import boards
import json
import os
from reading import Reading
from services.global_logger import logger
from services.data_logger import DataLogger
from sys import stdout
import time
import gc

# ---------------------------------------------------------------------
# TIMING CONFIGURATION
# ---------------------------------------------------------------------
SAMPLE_WINDOW_DURATION   = 5   # seconds to collect high-res data
SAMPLE_FREQ              = 5   # hz - how frequently samples are taken
SAMPLE_INTERVAL          = 1 / SAMPLE_FREQ
MODEM_RESPONSE_TIMEOUT   = 5   # seconds to wait for modem “OK” response
DEEPSLEEP_DURATION       = 5   # seconds to sleep between cycles

# ---------------------------------------------------------------------
# STATE DEFINITIONS
# ---------------------------------------------------------------------
MODE_MEASURE   = 0
MODE_TRANSMIT  = 1
MODE_DEEPSLEEP = 2

# ---------------------------------------------------------------------
# MODE IMPLEMENTATIONS (each returns the next mode)
# ---------------------------------------------------------------------
def measure_mode():
    """
        Collect high-resolution data for SAMPLE_WINDOW_DURATION,
        taking one sample every SAMPLE_INTERVAL seconds.
    """
    logger.info("Entering Measure Mode")
    logger.info("Setting up DataLogger")
    
    # 1. Create the directory if it doesn’t exist
    if "sample_data" not in os.listdir("/sd"):
        logger.info("Log directory doesn't exist...")
        logger.info("Creating log directory doesn't exist...")
        os.mkdir("/sd/logs")
        logger.info("Log directory created...")

    # 2. Create the file if it doesn’t exist
    logger.info("Creating sample file")
    sample_file = open(f"/sd/sample_data/{time.now()}")
    logger.info("Created sample file")
        
    dl = DataLogger()
    
    start_time = time.monotonic()
    while time.monotonic() - start_time < SAMPLE_WINDOW_DURATION:
        cpu_temperature = Reading(boards.logicboard.cpu.temperature, "C", "CPU Temperature")
        dl.log_reading(cpu_temperature)
        # ›› read sensor and buffer raw value (placeholder)
        #    reading = read_sensor()
        #    store reading to a file or list
        logger.info("Taking measurement")
        time.sleep(SAMPLE_INTERVAL)

    # Once the sampling window has elapsed, transition to TRANSMIT
    end_time = time.monotonic()
    logger.info(f"Took measurements for {end_time - start_time}s")
    logger.info("Exiting Measure Mode")
    return MODE_TRANSMIT


def transmit_mode():
    """
        Power on modem and wait up to MODEM_RESPONSE_TIMEOUT seconds
        or an “OK” response to confirm UART connectivity.
    """
    # ›› power on modem (placeholder)
    #    modem_power_enable(True)
    logger.info("Entering Transmit Mode")
    time.sleep(1)  # allow boot time

    start_time = time.monotonic()
    while time.monotonic() - start_time < MODEM_RESPONSE_TIMEOUT:
        # ›› send “AT” and check for “OK” (placeholder)
        #    if modem_is_responsive(): break
        time.sleep(0.1)

    # If no modem response, you might decide to skip transmit and sleep:
    #    return MODE_DEEPSLEEP

    # Otherwise, hand off to modem library to finish the rest of the transmit logic
    # (not shown here). When transmit is fully done, fall through and go to DEEPSLEEP.
    end_time = time.monotonic()
    logger.info(f"Took measurements for {end_time - start_time}s")
    logger.info("Exiting Transmit Mode")
    return MODE_DEEPSLEEP


def deepsleep_mode():
    """
        Power down all peripherals and sleep for DEEPSLEEP_DURATION seconds.
    """
    # ›› power off sensors and modem (placeholder)
    logger.info("Entering Deep Sleep Mode")
    time.sleep(DEEPSLEEP_DURATION)
    
    # After waking up, go back to MEASURE
    return MODE_MEASURE

# ---------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------
def main():
    current_mode = MODE_MEASURE

    while True:
        if current_mode == MODE_MEASURE:
            current_mode = measure_mode()

        elif current_mode == MODE_TRANSMIT:
            current_mode = transmit_mode()

        elif current_mode == MODE_DEEPSLEEP:
            current_mode = deepsleep_mode()

        # small pause before next iteration to prevent tight-loop CPU spin
        time.sleep(0.1)

if __name__ == "__main__":
    main()