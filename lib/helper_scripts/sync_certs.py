import bg95m3
import boards
import adafruit_logging as logging
import sys
import os

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

modem = boards.logicboard.CellularModem

ssl_context = bg95m3.SSL_Context(modem)

logger.info(f"Syncing modem certificates with local certificates")

logger.info(f"Uploading CA Cert: {os.getenv('CA_CERT_PATH')}")
ssl_context.upload_cacert()
logger.info(f"Uploading Device Certificate: {os.getenv('DEVICE_CERT_PATH')}")
ssl_context.upload_device_cert()
logger.info(f"Uploading Device Private Kay: {os.getenv('DEVICE_PRIVATE_KEY_PATH')}")
ssl_context.upload_device_private_key()
