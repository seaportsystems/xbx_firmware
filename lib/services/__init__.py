import adafruit_logging as logging
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import os
import socketpool
import ssl
import sys
import time
import wifi
import gc

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

# WiFi
logger.info("Connecting to WiFi")
try:
    wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
    logger.info(f"Successfully connected to WiFi with an IP address of: {wifi.radio.ipv4_address}")

except Exception as e:
    logger.error(f"Failed to connect to WiFi: {e}")

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

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
        client_id=os.getenv("DEVICE_ID"),
        username="",  # AWS IoT does not require a username
        password="",  # AWS IoT does not require a password
    )
    logger.info("Successfully initialized MQTT Client")
    mqtt_client.enable_logger(logging, 00, "mqttlogger")
    
    # Define MQTT event callbacks
    def connect(client, userdata, flags, rc):
        logger.info("Successfully connected to AWS IoT")

    def disconnect(client, userdata, rc):
        logger.info("Successfully disconnected from AWS IoT")

    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect

    # Connect to AWS IoT
    logger.info("Connecting to AWS IoT...")
    logger.info(f"Free blocks: {gc.mem_free()}")
    logger.info("Collecting garbage")
    gc.collect()
    logger.info(f"Free blocks: {gc.mem_free()}")
    mqtt_client.connect()

    # Publish a message
    mqtt_client.publish(f'XBX/os.getenv("DEVICE_ID")/log', "Connected to MQTT Broker")
    
except Exception as e:
    logger.warning(f"Failed to initialize MQTT client: {e}")