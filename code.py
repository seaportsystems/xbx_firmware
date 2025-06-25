from microcontroller import watchdog
from watchdog import WatchDogMode

watchdog.timeout = 8
watchdog.mode = None

import alarm
import boards
from json import dumps, loads
import os
from reading import Reading
from services.global_logger import logger
from services.data_logger import DataLogger
from services.device_manager import manager

from sys import stdout
import time
import gc

gc.enable()

# ---------------------------------------------------------------------
# COMMS CONFIGURATION
# ---------------------------------------------------------------------

DISABLE                  = 0
CELLULAR                 = 1
WIFI                     = 2
DEBUG                    = 3

COMMS_MODE               = CELLULAR

# ---------------------------------------------------------------------
# TIMING CONFIGURATION
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# SAMPLE MODES
# ---------------------------------------------------------------------
SM_TIMED                 = 0
SM_COUNT                 = 1

SAMPLE_MODE              = SM_COUNT
SAMPLES                  = 1
SAMPLE_WINDOW_DURATION   = 5   # seconds to collect high-res data
SAMPLE_FREQ              = 5   # hz - how frequently samples are taken
SAMPLE_INTERVAL          = 1 / SAMPLE_FREQ
WARMUP_DURATION          = 5
MODEM_RESPONSE_TIMEOUT   = 5   # seconds to wait for modem “OK” response
DEEPSLEEP_DURATION       = 5   # seconds to sleep between cycles

# ---------------------------------------------------------------------
# STATE DEFINITIONS
# ---------------------------------------------------------------------
MODE_WARMUP    = 0
MODE_MEASURE   = 1
MODE_TRANSMIT  = 2
MODE_DEEPSLEEP = 3

# ---------------------------------------------------------------------
# MODE IMPLEMENTATIONS (each returns the next mode)
# ---------------------------------------------------------------------
def warmup_mode():
    """
        Power on all devices, and wait for either WARMUP_DURATION or until modem and GPS are ready
    """
    logger.info(f"Entering warmup mode. Waiting either {WARMUP_DURATION} seconds or for fixes and connectivity on both Cellular Modem and GPS")
    start_time = time.monotonic()
    
    gps_ready = False
    modem_ready = False
    
    gps = manager.devices['attitudeboard.gps']
    modem = boards.logicboard.CellularModem
    
    while time.monotonic() - start_time < WARMUP_DURATION:
        gps_ready = gps.has_fix
        modem_ready = modem.is_comms_ready()
        
        if((gps_ready == True) and (modem_ready == True)):
            logger.info(f"GPS and Modem are ready, entering Measure Mode")
            break
        else:
            logger.info(f"GPS   Ready: {gps_ready}")
            logger.info(f"Modem Ready: {modem_ready}")
            time.sleep(1)
    else:
        logger.info(f"GPS and modem are not ready, entering Measure Mode")    
        
    return MODE_MEASURE

def measure_mode():
    """
        Collect high-resolution data for SAMPLE_WINDOW_DURATION,
        taking one sample every SAMPLE_INTERVAL seconds.
    """
    
    logger.info(f"Memory Free: {gc.mem_free()}")
    gc.collect()
    logger.info(f"Memory Free: {gc.mem_free()}")
    
    logger.info("Entering Measure Mode")
    logger.info("Setting up DataLogger")
    
    # 1. Create the directory if it doesn’t exist
    if "sample_data" not in os.listdir("/sd"):
        logger.info("Log directory doesn't exist...")
        logger.info("Creating log directory...")
        os.mkdir("/sd/sample_data")
        logger.info("Log directory created...")

    # 2. Create the file if it doesn’t exist
    
    sample_readings = []
    
    sample_filename = f"tmp.sample"
    logger.info(f"Creating sample file: {sample_filename}")
    sample_file = open(f"/sd/sample_data/{sample_filename}", "w")
    logger.info("Created sample file")
        
    dl = DataLogger()
    
    samples_taken = 0
    
    sensors = ['attitudeboard.barometer', 'attitudeboard.imu', 'attitudeboard.gps', 'atlassenseboard.conductivity', 'atlassenseboard.dissolvedoxygen', 'atlassenseboard.watertemperature']

    # logger.info(manager.all_devices())
    
    while samples_taken < SAMPLES:
        for sensor in sensors:
            all_readings = manager.devices[sensor].read()
            
            for r in all_readings.values(): 
                if(r is not None):
                    logger.info(f"{sensor} - {r}")
                    dl.log_reading(r)
                    sample_readings.append(r)
                else:
                    logger.warning(f"Reading from {sensor} was {r}")
    
        gc.collect()
        
        logger.info("Taking measurement")
        samples_taken = samples_taken + 1
        time.sleep(SAMPLE_INTERVAL)

    logger.info(f"Writing samples to: {sample_filename}")

    for r in sample_readings:
        if(r is not None):
            sample_file.write(dumps(r.__dict__))
            sample_file.write("\n")
        
    logger.info(f"Closing sample file: {sample_filename}")
    sample_file.close()
    logger.info(f"Closed sample file: {sample_filename}")
    
    # Once the sampling window has elapsed, transition to TRANSMIT
    logger.info("Exiting Measure Mode")
    logger.info(f"Memory Free: {gc.mem_free()}")
    gc.collect()
    logger.info(f"Memory Free: {gc.mem_free()}")
    
    return MODE_TRANSMIT

    
def transmit_mode():
    """
        Power on modem and wait up to MODEM_RESPONSE_TIMEOUT seconds
        or an “OK” response to confirm UART connectivity.
    """
    logger.info("Entering Transmit Mode")
    logger.info(f"Memory Free: {gc.mem_free()}")
    gc.collect()
    logger.info(f"Memory Free: {gc.mem_free()}")

    #unsent_samples_file = open("/sd/sample_data/uss.sample", "r")
    try:
        tmp_sample_file = open("/sd/sample_data/tmp.sample", "r")
        gc.collect()
    except Exception as e:
        logger.warning(f"Failed to open tmp sample file, exiting transmit mode: {e}")
        return MODE_DEEPSLEEP
        
    gc.collect()
    
    if(COMMS_MODE == DISABLE):
        logger.info("Comms are disabled")
        return MODE_DEEPSLEEP
     
    elif(COMMS_MODE == CELLULAR):
        start_time = time.monotonic()
        logger.info("Waiting for modem to warm up")
        
        while time.monotonic() - start_time < MODEM_RESPONSE_TIMEOUT:
            if boards.logicboard.CellularModem.is_comms_ready():
                logger.info(f"Modem Comms Ready: {boards.logicboard.CellularModem.is_comms_ready()}")
                logger.info(f"Setting up MQTT Connection")
                
                gc.collect()
                
                mqtt_client = boards.logicboard.CellularModem.create_mqtt_connection(os.getenv("DEVICE_ID"), os.getenv("AWS_IOT_ENDPOINT"))
                
                if(mqtt_client is None):
                    logger.warning(f"MQTT client didn't initialize")
                    return MODE_DEEPSLEEP
                
                if(not mqtt_client.is_open()):
                    mqtt_client.open()
                    gc.collect()
                
                if(not mqtt_client.is_connected()):
                    mqtt_client.connect()
                    gc.collect()
                        
                if(mqtt_client.is_connected()):
                    mqtt_client.publish(f"XBX/{os.getenv('DEVICE_ID')}/device", "Connected!")
                    gc.collect()

                    for line in tmp_sample_file:
                        jsonline = loads(line)
                        mqtt_client.publish(f"XBX/{os.getenv('DEVICE_ID')}/{jsonline['description']}", line)
                
                    mqtt_client.publish(f"XBX/{os.getenv('DEVICE_ID')}/device", "Disconnecting!")
                    mqtt_client.disconnect()
                    mqtt_client.close()
                    
                    return MODE_DEEPSLEEP
                
                break
            
            else:
                logger.info(f"Modem Responsive: {boards.logicboard.CellularModem.is_responsive()}")
                logger.info(f"Modem Registered: {boards.logicboard.CellularModem.is_registered_to_network()}")
                logger.info(f"Modem PDS Connected: {boards.logicboard.CellularModem.is_pds_connected()}")
                logger.info(f"Modem PDP Connected: {boards.logicboard.CellularModem.is_pdp_connected()}")
                logger.info(f"Modem Comms Ready: {boards.logicboard.CellularModem.is_comms_ready()}")
                
                logger.info("Waiting for modem to be ready for comms")
                time.sleep(1)            
            
        else:
            logger.warning("Modem failed to establish comms link...")
            return MODE_DEEPSLEEP
        
    elif(COMMS_MODE == WIFI):
        logger.warning(f"WiFi not currently supported")
        return MODE_DEEPSLEEP
    
    elif(COMMS_MODE == DEBUG):
        logger.info(f"Debug comms mode")
        return MODE_DEEPSLEEP
    
    else:
        logger.warning(f"Invalid comms mode: {COMMS_MODE}")
        return MODE_DEEPSLEEP
    
    # Otherwise, hand off to modem library to finish the rest of the transmit logic
    # (not shown here). When transmit is fully done, fall through and go to DEEPSLEEP.
    end_time = time.monotonic()
    logger.info("Exiting Transmit Mode")
    logger.info(f"Memory Free: {gc.mem_free()}")
    gc.collect()
    logger.info(f"Memory Free: {gc.mem_free()}")
    
    return MODE_DEEPSLEEP


def deepsleep_mode():
    """
        Power down all peripherals and sleep for DEEPSLEEP_DURATION seconds.
    """
    # ›› power off sensors and modem (placeholder)
    logger.info("Entering Deep Sleep Mode")
    
    # After waking up, go back to MEASURE
    # time_alarm = alarm.time.TimeAlarm(monotonic_time = time.monotonic() + DEEPSLEEP_DURATION)
    # alarm.exit_and_deep_sleep_until_alarms(time_alarm)
    time.sleep(DEEPSLEEP_DURATION)
    return MODE_WARMUP
    
    
# ---------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------
def main():
    current_mode = MODE_WARMUP

    while True:
        if current_mode == MODE_WARMUP:
            current_mode = warmup_mode()
        
        elif current_mode == MODE_MEASURE:
            current_mode = measure_mode()
        
        elif current_mode == MODE_TRANSMIT:
            current_mode = transmit_mode()

        elif current_mode == MODE_DEEPSLEEP:
            current_mode = deepsleep_mode()

        # small pause before next iteration to prevent tight-loop CPU spin
        time.sleep(0.1)
        
if __name__ == "__main__":
    main()