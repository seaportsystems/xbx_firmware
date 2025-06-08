import adafruit_logging as logging
import boards
from json import dumps, loads
import os
from reading import Reading
from services.global_logger import logger
from services.data_logger import DataLogger
from sys import stdout
import time
import gc

gc.enable()

# ---------------------------------------------------------------------
# COMMS CONFIGURATION
# ---------------------------------------------------------------------
CELLULAR                 = 0
WIFI                     = 1
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
    
    year, month, day, hour, minute, second, _, _, _ = time.localtime()
    sample_filename = f"SF{year:04d}{month:02d}{day:02d}T{hour:02d}{minute:02d}{second:02d}"
    logger.info(f"Creating sample file: {sample_filename}")
    sample_file = open(f"/sd/sample_data/{sample_filename}", "w")
    logger.info("Created sample file")
        
    dl = DataLogger()
    
    samples_taken = 0
    while samples_taken < SAMPLES:
        accelerations = Reading(boards.attitudeboard.imu.accelerations, "m/s^2", "Acceleration Vector")
        dl.log_reading(accelerations)
        sample_readings.append(accelerations)
        
        rotations = Reading(boards.attitudeboard.imu.rotations, "rad/s", "Angular Velocity")
        dl.log_reading(rotations)
        sample_readings.append(rotations)
        
        magnetics = Reading(boards.attitudeboard.imu.magnetics, "uT", "Magnetic Field Vector")
        dl.log_reading(magnetics)
        sample_readings.append(magnetics)
        
        pressure = Reading(boards.attitudeboard.barometer.pressure, "hPa", "Pressure")
        dl.log_reading(pressure)
        sample_readings.append(pressure)
        
        salinity = Reading(boards.atlassenseboard.EZO_EC.EC, "uS/cm", "Salinity")
        dl.log_reading(salinity)
        sample_readings.append(salinity)
        
        dissolved_oxygen = Reading(boards.atlassenseboard.EZO_DO.MGL, "mg/l", "Dissolved Oxygen")
        dl.log_reading(dissolved_oxygen)
        sample_readings.append(dissolved_oxygen)
        
        water_temperature = Reading(boards.atlassenseboard.EZO_RTD.T, "C", "Water Temperature")
        dl.log_reading(water_temperature)
        sample_readings.append(water_temperature)
        
        ambient_temperature = Reading(boards.attitudeboard.barometer.temperature, "C", "Ambient Temperature")
        dl.log_reading(ambient_temperature)
        sample_readings.append(ambient_temperature)
        
        cpu_temperature = Reading(boards.logicboard.cpu.temperature, "C", "CPU Temperature")
        dl.log_reading(cpu_temperature)
        sample_readings.append(cpu_temperature)
    
        gc.collect()
        
        logger.info("Taking measurement")
        samples_taken = samples_taken + 1
        time.sleep(SAMPLE_INTERVAL)

    logger.info(f"Writing samples to: {sample_filename}")

    for r in sample_readings:
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
    logger.info(f"Memory Free: {gc.mem_free()}")
    gc.collect()
    logger.info(f"Memory Free: {gc.mem_free()}")
    # ›› power on modem (placeholder)
    #    modem_power_enable(True)
    logger.info("Entering Transmit Mode")
    time.sleep(1)  # allow boot time

    samples = os.listdir("/sd/sample_data/")
    
    for sample in samples:
        with open(f"/sd/sample_data/{sample}", "r") as sample_file:
            for line in sample_file:
                print(line)
                jsonline = loads(line)
                logger.info(f"Publishing: {line} to XBX/{os.getenv('DEVICE_ID')}/{jsonline['description']}")
                
        
        gc.collect()
                
    if(COMMS_MODE == CELLULAR):
        start_time = time.monotonic()
        logger.info("Waiting for modem to warm up")
        while time.monotonic() - start_time < MODEM_RESPONSE_TIMEOUT:
            if boards.logicboard.CellularModem.is_comms_ready():
                logger.info(f"Modem Comms Ready: {boards.logicboard.CellularModem.is_comms_ready()}")
                logger.info(f"Setting up MQTT Connection")
                mqtt_client = boards.logicboard.CellularModem.create_mqtt_connection(os.getenv("DEVICE_ID"), os.getenv("AWS_IOT_ENDPOINT"))
                
                if(not mqtt_client.is_open()):
                    try:
                        print("Attempting to open MQTT Connection")
                        mqtt_client.open()
                    except ConnectionError as exception:
                        print("Failed to open MQTT socket")
                
                if(not mqtt_client.is_connected()):
                    try:
                        print("Attempting to establish MQTT Connection")
                        mqtt_client.connect()
                    except:
                        print("Failed to connect...")
                        
                if(mqtt_client.is_connected()):
                    try:
                        print(f"Attempting to publish message to: XBX/{os.getenv('DEVICE_ID')}/device")
                        mqtt_client.publish(f"XBX/{os.getenv('DEVICE_ID')}/device", "Connected!")
    
                        for sample in samples:
                            with open(f"/sd/sample_data/{sample}", "r") as sample_file:
                                for line in sample_file:
                                    jsonline = loads(line)
                                    mqtt_client.publish(f"XBX/{os.getenv('DEVICE_ID')}/{jsonline['description']}", line)
                                    logger.info(f"Published: {line} to XBX/{os.getenv('DEVICE_ID')}/{jsonline['description']}")
                                    
                            logger.info(f"Deleting: {sample}")
                            os.remove(f"/sd/sample_data/{sample}")
                            logger.info(f"Deleted: {sample}")
                                    
                    except Exception as e:
                        print(f"Failed to publish: {e}")
            
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
        try:
            logger.info("Initializing Wi-FI and MQTT")
            from services.wifi_mqtt import mqtt_client
            
            logger.info("Publishing...")
            mqtt_client.publish(topic=f"XBX/{os.getenv('DEVICE_ID')}/log/", msg="Testing...")
            logger.info("Done publishing?")
            
        except Exception as e:
            logger.info(f"Welp... we tried *shrugs*: {e}")
    else:
        logger.warning(f"Invalid comms mode: {COMMS_MODE}")
    
    # If no modem response, you might decide to skip transmit and sleep:
    #    return MODE_DEEPSLEEP

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
            logger.info(f"Exited Measure Mode")
        
        elif current_mode == MODE_TRANSMIT:
            current_mode = transmit_mode()

        elif current_mode == MODE_DEEPSLEEP:
            current_mode = deepsleep_mode()

        # small pause before next iteration to prevent tight-loop CPU spin
        time.sleep(0.1)

if __name__ == "__main__":
    main()