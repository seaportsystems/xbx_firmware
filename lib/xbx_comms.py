import adafruit_logging as logging
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
# Start logging to file
try:
    logger.addHandler(logging.FileHandler(f'sd/{__name__}.log', 'a'))
    logger.info(f"Logging to /sd/{__name__}.log")
except Exception as e:
    logger.warning(f"Failed to add FileHandler to logger: {e}")
logger.setLevel(logging.DEBUG)

import os
import rtc
import socketpool
import ssl
import time
import wifi
            
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_ntp as NTP
import adafruit_requests as requests

# WiFi
logger.info("Connecting to WiFi")
try:
    wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
    logger.info(f"Successfully connected to WiFi with an IP address of: {wifi.radio.ipv4_address}")

except Exception as e:
    logger.error(f"Failed to connect to WiFi: {e}")

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

# Sync time with NTP server
try:
    logger.info(f"Syncing time with NTP server")
    ntp_instance = NTP.NTP(pool, server="pool.ntp.org", tz_offset=0)  # Set tz_offset as per your timezone
    rtc_instance = rtc.RTC()
    rtc_instance.datetime = ntp_instance.datetime
    current_time = rtc_instance.datetime
    logger.info(f"Successfully set device RTC to: {current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}")
except Exception as e:
    logger.warning(f"Failed to sync time wtih NTP server: {e}")

# Load the AWS CA certificate
with open(os.getenv('CA_CERT_PATH'), "rb") as ca_file:
    ca_cert = ca_file.read()
    logger.info(f"Device Cert: {len(ca_cert)}")

# Configure SSL context with certificates and keys
ssl_context.load_verify_locations(cadata=ca_cert)  # AWS CA certificate
ssl_context.load_cert_chain(certfile=os.getenv('DEVICE_CERT_PATH'), keyfile=os.getenv('DEVICE_PRIVATE_KEY_PATH'))  # Device cert and private key
logger.info("Set SSL Context")

# MQTT client setup
try:
    logger.info("Initializing MQTT client")
    mqtt_client = MQTT.MQTT(
        broker=os.getenv('AWS_IOT_ENDPOINT'),  # Replace with your AWS IoT endpoint
        port=8883,  # AWS IoT uses port 8883 for MQTT over TLS
        socket_pool=pool,
        ssl_context=ssl_context,
        is_ssl=True,
        username="",  # AWS IoT does not require a username
        password="",  # AWS IoT does not require a password
    )
    logger.info("Successfully initialized MQTT Client")

    # Define MQTT event callbacks
    def connect(client, userdata, flags, rc):
        logger.info("Successfully connected to AWS IoT")

    def disconnect(client, userdata, rc):
        logger.info("Successfully disconnected from AWS IoT")

    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect

    # Connect to AWS IoT
    logger.info("Connecting to AWS IoT...")
    mqtt_client.connect()

    # Publish a message
    mqtt_client.publish("xbxdevkit/system_log", "Connected to MQTT Broker")
    
except Exception as e:
    logger.warning(f"Failed to initialize MQTT client: {e}")