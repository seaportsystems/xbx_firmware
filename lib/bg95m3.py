from microcontroller import watchdog
import board
import digitalio
import gc
import os
import re
import time

from services.global_logger import logger

gc.enable()

from random import randint

class Status:
    OK = 0
    ERROR = 1
    TIMEOUT = 2
    ONGOING = 3
    UNKNOWN = 99

class SSL_Context:
    def __init__(self, modem, ssl_context_id=2):
        self.modem = modem
        self.ssl_context_id = ssl_context_id
        self.sslversion = 4
        self.ciphersuite = '0XFFFF'
        self.cacert = 'cacert.pem'
        self.clientcert = 'device_cert.pem'
        self.clientkey = 'device_private_key.pem'
        self.seclevel = 2
        self.session = 0
        self.sni = 1
        self.checkhost = 0
        self.ignorelocaltime = 1
        self.renegotiation = 0
        
        logger.info("Syncing certs...")
        try:
            self.upload_cacert()
            self.upload_device_cert()
            self.upload_device_private_key()
        except Exception as e:
            logger.info(f"Failed to automatically sync certs")
            logger.info("Try running: 'from helper_scripts import sync_certs' from the REPL")
    
    def upload_cacert(self, new_ca_cert_path=os.getenv('CA_CERT_PATH')):
        #Delete old cacert.pem
        self.modem.delete_file_from_modem('cacert.pem')
        
        #Upload new cacert.pem
        with open(new_ca_cert_path, "r") as new_ca_cert_file:
            new_ca_cert = new_ca_cert_file.read()
            
            try:
                self.modem.upload_file_to_modem('cacert.pem', new_ca_cert)
            except Exception as e:
                logger.info(f"Error uploading new CA Cert to modem: {e}")
    
    def upload_device_cert(self, new_device_cert_path=os.getenv('DEVICE_CERT_PATH')):
        #Delete old device_cert.pem
        self.modem.delete_file_from_modem('device_cert.pem')
        
        #Upload new device_cert.pem
        with open(new_device_cert_path, "r") as new_device_cert_file:
            new_device_cert = new_device_cert_file.read()
            
            try:
                self.modem.upload_file_to_modem('device_cert.pem', new_device_cert)
            except Exception as e:
                logger.info(f"Error uploading new Device Cert to modem: {e}")
    
    def upload_device_private_key(self, new_device_private_key_path=os.getenv('DEVICE_PRIVATE_KEY_PATH')):
        #Delete old device_private_key.pem
        self.modem.delete_file_from_modem('device_private_key.pem')
        
        #Upload new private_key.pem
        with open(new_device_private_key_path, "r") as new_device_private_key_file:
            new_device_private_key = new_device_private_key_file.read()
            
            try:
                self.modem.upload_file_to_modem('device_private_key.pem', new_device_private_key)
            except Exception as e:
                logger.info(f"Error uploading new Device private_key to modem: {e}")
            
    def set_context(self):
        logger.info("Setting SSL Context")
    
        self.set_parameter("sslversion", self.sslversion)
        self.set_parameter("ciphersuite", self.ciphersuite)
        
        #TODO get self.set_parameter working for values that need to be enapsulated in quotes
        self.modem.send_comm_get_response('AT+QSSLCFG="cacert",2,"cacert.pem"')
        self.modem.send_comm_get_response('AT+QSSLCFG="clientcert",2,"device_cert.pem"')
        self.modem.send_comm_get_response('AT+QSSLCFG="clientkey",2,"device_private_key.pem"')
        
        self.set_parameter("seclevel", self.seclevel)
        self.set_parameter("session", self.session)
        self.set_parameter("sni", self.sni)
        self.set_parameter("checkhost", self.checkhost)
        self.set_parameter("ignorelocaltime", self.ignorelocaltime)
        self.set_parameter("renegotiation", self.renegotiation)

    def set_parameter(self, key, value):
        response = self.modem.send_comm_get_response(f'AT+QSSLCFG="{key}", {self.ssl_context_id}, {value}')

        #Check that the open connection command was RECEIVED AND PARSED successfully
        if(response['status_code'] == Status.OK):
            logger.info(f"Successfully set {key} to {value}...")
            return True
        
        elif(response['status_code'] == Status.ERROR):
            logger.info("response")
            raise RuntimeError(f'Error setting SSL parameter {key} to {value}: AT+QSSLCFG="{key}", {self.ssl_context_id}, {value}')
        else:
            raise RuntimeError(f"Something else weird happened: {response}")
            
class MQTT_Socket:
    def __init__(self, modem, client_id, hostname, port, socket_id):
        self.modem = modem
        
        self.client_id = client_id
        self.hostname = hostname
        self.port = port
        self.socket_id = socket_id  #client_idx in modem docs
    
        #Set default SSL context to use SSL/TLS and certificates
        default_ssl_context = SSL_Context(self.modem, ssl_context_id=2)
        default_ssl_context.set_context()
        
        #Use SSL context 2
        logger.info("Setting SSL Context")
        self.modem.send_comm_get_response(f'AT+QMTCFG="ssl",{self.socket_id},1,2')
        
    #open socket, connect, do your thing, disconnect, close
    def open(self):
        logger.info("Openning socket")
        try:
            if(not self.modem.is_comms_ready()):
                logger.warning(f"Failed to open the socket: modem isn't comms ready")
            
            logger.info(f'Open Command: AT+QMTOPEN={self.socket_id},"{self.hostname}",{self.port}')
            response = self.modem.send_comm_get_response(f'AT+QMTOPEN={self.socket_id},"{self.hostname}",{self.port}', timeout=60)

            #Check that the open connection command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting for socket to open...")
                pattern = re.compile(r"^\+QMTOPEN: (.*)$")

                #Wait for a +QMTOPEN: message
                open_result_response = self.modem.wait_for_response(pattern, timeout=60)
                logger.info(f"Open Result Response: {open_result_response}")           
                logger.info("Successfully opened socket")
                
            else:
                logger.warning(f"Potentially failed to open socket: {response}")
                               
        except Exception as e:
            logger.warning(f"Failed to open the socket: {e}")
            
    def close(self):
        logger.info("Closing socket")
        try:   
            #Check for open connections
            if (self.is_connected()):
                logger.warning(f"Socket is still connected, attempting to disconnect")
                self.disconnect()
                
            time.sleep(1)
            
            if(not self.is_open()):
                logger.warning(f"Socket is already closed")
                return True
                
            #Try to open the connection
            response = self.modem.send_comm_get_response(f'AT+QMTCLOSE={self.socket_id}')

            #Check that the open connection command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting for connection to close...")
                pattern = re.compile(r"^\+QMTCLOSE: (.*)$")

                #Wait for a +QMTOPEN: message to check result of attempting to open connection
                close_result_response = self.modem.wait_for_response(pattern, timeout=30)

                if(close_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data([close_result_response['response_line']], pattern)
                    parsed_response = parsed_responses[0]
                    
                    if(int(parsed_response[1]) == 0):
                        logger.info(f"Successfully closed socket: {parsed_response[0]}: {parsed_response[1]}")
                        return True
                    else:
                        logger.warning(f"Failed to close socket: {parsed_response[0]}: {parsed_response[1]}")
                        return False
                else:
                    logger.warning(f"Failed to close socket, something weird...")
                    logger.warning(f"{close_result_response}")
                    return False
                
        except Exception as e:
            logger.warning(f"Failed to close the socket: {e}")
    
    def connect(self, retries=3):
        try:
            if(not self.is_open()):
                logger.warning(f"Socket isn't open")
                logger.info(f"Attempting to open socket")
                self.open()
            
            while retries > 0:
                logger.info(f"Connecting to MQTT Broker. Retries remaining: {retries}")
                #Try to connect to broker
                logger.info(f'Connecting with command: AT+QMTCONN={self.socket_id},"{self.client_id}"')
                response = self.modem.send_comm_get_response(f'AT+QMTCONN={self.socket_id},"{self.client_id}"', timeout=30)
                
                #Check that the connect command was RECEIVED AND PARSED successfully
                if(response['status_code'] == Status.OK):
                    logger.info("Waiting to establish connection to broker...")
                    pattern = re.compile(r"^\+QMTCONN: (.*)$")
                    qmtstat_pattern = re.compile(r"^\+QMTSTAT: (.*)$")
                    
                    #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                    connect_result_response = self.modem.wait_for_response(pattern, secondary_pattern = qmtstat_pattern, timeout=120)
                    
                    logger.info(f"Connect Result Response: {connect_result_response}")

                    if(connect_result_response['status_code'] == Status.OK):
                        logger.info(f"Status OK")
                        logger.info(f"Data: {response['data']}")
                        parsed_responses = self.modem.parse_response_data([connect_result_response['response_line']], pattern)
                        logger.info(f"Parsed Response: {parsed_responses}")
                        parsed_response = parsed_responses[0]
                        logger.info("Connected!")

                        return {'socket_id': parsed_response[0], 'result': parsed_response[1]}
                    else:
                        logger.warning(f"Unknown connection result: {connect_result_response}")
                        
                else:
                    logger.info(f"Error connecting: {response}")
                    logger.info("Retrying in 3 seconds...")
                    #logger.info(f"Feeding watchdog")
                    watchdog.feed()
                    time.sleep(3)
                    retries = retries - 1
                    
        except Exception as e:
            logger.warning(f"Failed to connect to MQTT Broker: {e}")
    
    def disconnect(self):
        try:
            #Try to connect to broker
            response = self.modem.send_comm_get_response(f'AT+QMTDISC={self.socket_id}')

            #Check that the connect command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting to confirm disconnection with broker...")
                pattern = re.compile(r"^\+QMTDISC: (.*)$")

                #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                connect_result_response = self.modem.wait_for_response(pattern, timeout=10)

                if(connect_result_response['status_code'] == Status.OK):
                    logger.info("Successfully sent disconnect command")
                    # parsed_responses = self.modem.parse_response_data(response['data'], pattern)
                    # parsed_response = parsed_responses[0]
                    
                    disconnected_pattern = re.compile(r"^\+QMTSTAT: (.*)$")
                    logger.info("Waiting for QMSTAT: +0,5")
                    disconnected_response = self.modem.wait_for_response(disconnected_pattern, timeout=30)
                    logger.info(f"disconnect_response: {disconnected_response}")
                    parsed_disconnected_response = self.modem.parse_response_data([disconnected_response['response_line']], disconnected_pattern)[0]
                    logger.info(f"parsed_disconnected_response: {parsed_disconnected_response}")
                    
                    if(int(parsed_disconnected_response[1]) == 5):
                        logger.info(f"Disconnected \t {disconnected_response}")
                    else:
                        logger.info(f"Have to force close...")
                        self.close()
                else:
                    #Failed to set
                    pass
                
        except Exception as e:
            logger.warning(f"Failed to disconnect from MQTT Broker: {e}")
        
    def subscribe(self, topic, qos):
        try:
            if(not self.is_connected()):
                raise RuntimeError("MQTT isn't connected")
            
            msg_id = randint(0,65535)
            
            response = self.modem.send_comm_get_response(f'AT+QMTSUB={self.socket_id},{msg_id},"{topic}",{qos}')

            #Check that the subscribe command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting to confirm subscription with broker...")
                pattern = re.compile(r"^\+QMTSUB: (.*)$")

                #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                subscribe_result_response = self.modem.wait_for_response(pattern, timeout=10)

                if(subscribe_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data(response['data'], pattern)
                    logger.info(parsed_responses)
                    parsed_response = parsed_responses[0]

                    if(parsed_response[2] == 0):
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2], 'granted_qos_level': parsed_response[3]}
                    if(parsed_response[2] == 1):
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2], 'packet_retries': parsed_response[3]}
                    if(parsed_response[2] == 2):
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2]}
                else:
                    #Failed to set
                    pass
        except Exception as e:
            logger.warning(f"Failed to subscribe to topic {topic}: {e}")

    def unsubscribe(self, topic):
        try:
            if(not self.is_connected()):
                raise RuntimeError("MQTT isn't connected")
            
            msg_id = randint(0,65535)
            
            response = self.modem.send_comm_get_response(f'AT+QMTUNS={self.socket_id},{msg_id},"{topic}"')

            #Check that the subscribe command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting to confirm unsubscription with broker...")
                pattern = re.compile(r"^\+QMTUNS: (.*)$")

                #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                unsubscribe_result_response = self.modem.wait_for_response(pattern, timeout=10)

                if(unsubscribe_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data(response['data'], pattern)
                    parsed_response = parsed_responses[0]
                    
                    if(parsed_response[2] == 0):
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2]}
                    
        except Exception as e:
            logger.warning(f"Failed to unsubscribe from topic {topic}: {e}")
            
    def publish(self, topic, msg, qos=1, retain=0):
        try:
            if(not self.is_connected()):
                raise RuntimeError("MQTT isn't connected")
            
            msg_id = randint(0,65535)
            logger.info(f"Publishing message: {msg} to topic: {topic} with a QoS of {qos}")
            response = self.modem.send_comm_get_response(f'AT+QMTPUBEX={self.socket_id},{msg_id},{qos},{retain},"{topic}","{msg}"')

            #Check that the subscribe command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info(f"Successfully sent publish command")
                
                logger.info("Waiting to confirm publish with broker...")
                pattern = re.compile(r"^\+QMTPUB: (.*)$")

                #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                publish_result_response = self.modem.wait_for_response(pattern, timeout=10)

                if(publish_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data([publish_result_response['response_line']], pattern)
                    parsed_response = parsed_responses[0]

                    if(parsed_response[2] == 1):
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2], 'packet_retries': parsed_response[3]}
                    else:
                        return {'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'result': parsed_response[2]}
                else:
                    #Failed to set
                    pass
            else:
                logger.warning(f"Failed to send publish command")
                
        except Exception as e:
            logger.warning(f"Failed to publish to topic: {e}")

    def read(self):
        try:
            if(not self.is_connected()):
                raise RuntimeError("MQTT isn't connected")
            
            response = self.modem.send_comm_get_response(f'AT+QMTRECV={self.socket_id}')

            #Check that the subscribe command was RECEIVED AND PARSED successfully
            if(response['status_code'] == Status.OK):
                logger.info("Waiting for read...")
                pattern = re.compile(r"^\+QMTRECV: (.*)$")

                #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                recv_result_response = self.modem.wait_for_response(pattern, imeout=10)

                if(recv_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data(response['data'], pattern)
                    logger.info(parsed_responses)
                    messages = [{'socket_id': parsed_response[0], 'msgID': parsed_response[1], 'topic': parsed_response[2], 'payload_len': parsed_response[3], 'payload': parsed_response[4]} for parsed_response in parsed_responses]

                    return messages
        except Exception as e:
            logger.warning(f"Failed to read message from topic: {e}")
    
    def get_mqtt_socket_state(self):
        response = self.modem.send_comm_get_response(f'AT+QMTOPEN?')
        
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QMTOPEN: (.*)$")
            parsed_responses = self.modem.parse_response_data(response['data'], pattern)
            
            open_socket_ids = [int(parsed_response[0]) for parsed_response in parsed_responses]
            
            if(self.socket_id in open_socket_ids):
                return True
            else:
                return False
        
        else:
            logger.info("Error")
    
    def is_open(self):
        return self.get_mqtt_socket_state()
    
    def get_mqtt_connection_state(self):
        response = self.modem.send_comm_get_response(f'AT+QMTCONN?')
        
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QMTCONN: (.*)$")
            parsed_responses = self.modem.parse_response_data(response['data'], pattern)
            socket_states = {}
            
            for parsed_response in parsed_responses:
                socket_states[int(parsed_response[0])] = int(parsed_response[1])
            
            if(self.socket_id in socket_states.keys()):
                return socket_states[self.socket_id]
            else:
                return False
        
        else:
            logger.info("Error")
            
    def is_connected(self):
        state = self.get_mqtt_connection_state()
        
        if state == 3:
            return True
        else:
            return False
        
class BG95M3:
    """Class for handling AT communication with modem"""
    def __init__(self, uart_bus):
        self.uart_bus = uart_bus
        self.power_button = digitalio.DigitalInOut(board.GP17)
        self.power_button.direction = digitalio.Direction.OUTPUT
        self.power_status = digitalio.DigitalInOut(board.GP20)
        self.power_status.direction = digitalio.Direction.INPUT

        self.power_on()

        retries = 0
        max_retries = 3

        while not self.check_communication():
            logger.info("Waiting for device to initialize")
            retries += 1
            if retries >= max_retries:
                logger.info("Communication failed. Restarting modem.")
                self.restart(graceful=False)
                retries = 0
            time.sleep(1)

        logger.info("Finding inherited sockets")
        inherited_sockets = self.get_open_mqtt_sockets()
        
        for i in inherited_sockets:
            logger.info(f"Inherited socket: {i}")
            try:
                response = self.modem.send_comm_get_response(f'AT+QMTCLOSE={i['socket_id']}')
                
                pattern = re.compile(r"^\+QMTCLOSE: (.*)$")
                
                #Wait for a +QMTOPEN: message to check result of attempting to open connection
                close_result_response = self.modem.wait_for_response(pattern, timeout=30)

                if(close_result_response['status_code'] == Status.OK):
                    parsed_responses = self.modem.parse_response_data([close_result_response['response_line']], pattern)
                    parsed_response = parsed_responses[0]
                    
                    if(int(parsed_response[1]) == 0):
                        logger.info(f"Successfully closed socket: {parsed_response[0]}: {parsed_response[1]}")
                    else:
                        logger.warning(f"Failed to close socket: {parsed_response[0]}: {parsed_response[1]}")
                else:
                    logger.warning(f"Failed to close socket{i['socket_id']}")
                    logger.warning(f"{close_result_response}")
                    
            except Exception as e:
                logger.info(f"Failed to close inherited sockets: {e}")
        
        gc.collect()
        # Clear any existing SSL contexts
        logger.info("Clearing existing SSL contexts...")
        for ctx_id in range(0, 6):
            try:
                self.send_comm_get_response(f'AT+QSSLCLOSE={ctx_id}', timeout=5)
            except:
                pass
        
        gc.collect()
        
        logger.info("Setting Echo Mode to OFF")
        self.send_comm_get_response("ATE0")
        
        gc.collect()
        
        logger.info(f"Device ICCID: {self.get_iccid()}")
        logger.info("Device is ready")
        gc.collect()
        
    #---SUPER HIGH LEVEL CHECKERS---#
    def is_responsive(self):
        return self.check_communication()
    
    def is_registered_to_network(self):
        network_registration_status = self.get_network_registration_status()
        
        stat = network_registration_status.get('stat')
        
        if stat in [1, 5]:
            return True
        else:
            return False
        
    def is_pds_connected(self):
        packet_service_status = self.get_packet_service_status()
        
        connected = packet_service_status.get('state')
        
        if connected:
            return True
        else:
            return False
    
    def is_pdp_connected(self):
        pdp_status = self.get_pdp_status()
        connected = pdp_status[0].get('state')
        if connected:
            return True
        else:
            return False
        
    def is_comms_ready(self):
        if self.is_responsive() and self.is_registered_to_network() and self.is_pds_connected() and self.is_pdp_connected():
            return True
        else:
            return False
        
    #---HARDWARE---#
    def power_status_check(self):
        """
        Checks the current state of the modem (on/off).
        """
        return not self.power_status.value

    def toggle_power(self):
        """
        Toggles the modem's power button
        Returns: nothing
        """
        self.power_button.value = True
        time.sleep(1)
        self.power_button.value = False
        time.sleep(0.5)
        
    def power_on(self):
        """
        Turns the modem on by calling the power_toggle function with True.
        """
        current_state = self.power_status_check()
        
        if current_state == True:        
            logger.info("Device is already on")
        else:
            self.toggle_power()

    def power_off(self, graceful=True):
        """
        Turns the modem off by calling the power_toggle function with False.
        """
        current_state = self.power_status_check()
        
        if current_state == False:        
            logger.info("Device is already off")
        else:
            if(graceful):
                response = self.send_comm_get_response(f'AT+QPOWD', timeout=5)
                
                #Check that the connect command was RECEIVED AND PARSED successfully
                if(response['status_code'] == Status.OK):
                    logger.info("Waiting to establish connection to broker...")
                    pattern = re.compile(r"\+?POWERED\s+DOWN")
                    
                    #Wait for a +QMTCONN: message to check result of attempting to connect to broker
                    power_down_response = self.wait_for_response(pattern, timeout=120)
                    
                    if(power_down_response['status_code'] == Status.OK):
                        logger.info("Got good power down response from modem")
                        self.toggle_power()

            self.toggle_power()

    def restart(self, graceful=True):
        """
        Turns the modem off, then turns it back on again
        """
        self.power_off(graceful)
        time.sleep(1)
        self.power_on()

    #---BASIC COMMS---#
    def send_comm(self, command, endline='\r'):
        try:
            self.uart_bus.reset_input_buffer()
            self.uart_bus.write(f"{command}{endline}".encode('utf-8'))
        except:
            pass

    def get_response(self, timeout=5):
        """
        Waits for a status response code: OK, ERROR, +CME ERROR: , +CMS ERROR: and returns all response lines before it
        """
        response = ""
        response_lines = []

        timer = time.time()
        
        ok_pattern = re.compile(r"^OK$")
        error_pattern = re.compile(r"ERROR$")
        cme_error_pattern = re.compile(r"^\+CME ERROR: (.*)$")
        cms_error_pattern = re.compile(r"^\+CMS ERROR: (.*)$")
        
        #Waits for OK, ERROR or +CME ERROR: message, or returns timeout error
        while True:
            #logger.info(f"Feeding watchdog")
            watchdog.feed()
            time.sleep(0.1)  # wait for new chars

            if time.time() - timer < timeout:
                while self.uart_bus.in_waiting:
                    try:
                        response = self.uart_bus.read(self.uart_bus.in_waiting).decode("utf-8")
                    except:
                        pass
            else:
                return {"status": "Timeout", "status_code": Status.TIMEOUT, "data": [], "response_line": ""}
            
            #if new data from the buffer isn't None, split the data by line and add to response_lines
            if response != "":
                response_lines.extend([x for x in response.split("\r\n") if x != ""])
                response = ""

            for index, line in enumerate(response_lines):
                if ok_pattern.match(line):
                    # logger.info("Matched: OK")
                    return {"status": line, "status_code": Status.OK, "data": response_lines[:index], "response_line": line}
                elif error_pattern.match(line):
                    logger.info("Matched: ERROR")
                    return {"status": line, "status_code":Status.ERROR, "data": response_lines[:index], "response_line": line}
                elif cme_error_pattern.match(line):
                    logger.info("Matched: CME ERROR")
                    return {"status": line, "status_code":Status.ERROR, "data": response_lines[:index], "response_line": line}
                elif cms_error_pattern.match(line):
                    logger.info("Matched: CMS ERROR")
                    return {"status": line, "status_code":Status.ERROR, "data": response_lines[:index], "response_line": line}

    def wait_for_response(self, response_pattern, secondary_pattern=None, timeout=5):
        """
        Waits up to timeout duration, for a line from the uart_bus, matching regex response pattern
        """
        response = ""
        response_lines = []

        timer = time.time()
        
        #Waits for OK, ERROR or +CME ERROR: message, or returns timeout error
        while True:
            #logger.info(f"Feeding watchdog")
            watchdog.feed()
            time.sleep(0.1)  # wait for new chars

            if time.time() - timer < timeout:
                while self.uart_bus.in_waiting:
                    try:
                        i = self.uart_bus.in_waiting
                        response = self.uart_bus.read(self.uart_bus.in_waiting).decode("utf-8")
                        logger.info(f"Read {i} bytes")
                    except:
                        pass
            else:
                return {"status": "Timeout", "status_code": Status.TIMEOUT, "data": [], "raw_response": ""}
            
            #if new data from the buffer isn't None, split the data by line and add to response_lines
            if response != "":
                response_lines.extend([x for x in response.split("\r\n") if x != ""])
                response = ""

            logger.info(f"In waiting for a respone, we have {len(response_lines)}")
            for r in response_lines:
                logger.info(f"{r}")
            
            for index, line in enumerate(response_lines):
                if response_pattern.match(line):
                    logger.info(f"Matched primary response pattern")
                    return {"status": "OK", "status_code": Status.OK, "data": response_lines[:index], "response_line": line}
                elif secondary_pattern is not None:
                    if secondary_pattern.match(line):
                        logger.info(f"Matched secondary response pattern")
                        return {"status": "Unknown", "status_code": Status.UNKNOWN, "data": response_lines[:index], "response_line": line}

    def parse_response_data(self, data, response_pattern):
        """
        Parses data for lines that match the response pattern, if a line matches the response pattern, it's data is split by ',' and appended to return data
        """

        matched_data = []
        for line in data:
            matched_line = response_pattern.match(line)
            if(matched_line):
                stripped_line = matched_line.group(1)
                split_line = [x.strip('"') for x in stripped_line.split(",")]
                matched_data.append(split_line)
        
        return matched_data

    def send_comm_get_response(self, command, endline='\r', timeout=5):
        self.send_comm(command, endline)
        time.sleep(.1)
        
        return self.get_response(timeout=timeout)
    
    def check_communication(self):
        """
        Function for checking modem communication
        """
        
        response = self.send_comm_get_response("AT")
        if(response['status_code'] == Status.OK):
            return True
        else:
            return False
    
    @property
    def is_ready():
        pass
    
    #---BASIC DEVICE CONFIG---#
    def set_urc_indication_config(self, urc_type, enable, save=1):
        response = self.send_comm_get_response(f"AT+QINDCFG={urc_type},{enable},{save}")
        parsed_response = self.parse_single_response(response, "+QINDCFG: ")
        return parsed_response
    
    #---BASIC CELLULAR INFO---#
    def get_imei(self):
        response = self.send_comm_get_response("AT+GSN")
        if(response['status_code'] == Status.OK):
            return int(response['data'][0])
    
    def get_imsi(self):
        response = self.send_comm_get_response("AT+CIMI")
        if(response['status_code'] == Status.OK):
            return int(response['data'][0])
    
    def get_iccid(self):
        response = self.send_comm_get_response("AT+QCCID")

        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QCCID: (.*)$")
            for line in response['data']:
                matched = pattern.match(line)
                if matched:
                    return int(matched.group(1))
    
    def get_network_registration_status(self):
        response = self.send_comm_get_response("AT+CREG?")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CREG: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            return {"n": int(parsed_responses[0][0]), "stat": int(parsed_responses[0][1])}
        
    
    def get_current_operator_status(self):
        response = self.send_comm_get_response("AT+COPS?")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+COPS: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            if(len(parsed_responses[0]) == 4):
                return {"mode": parsed_responses[0][0], "format": parsed_responses[0][1], "operator": parsed_responses[0][2], "act": parsed_response[3]}

            else:
                return {"mode": parsed_responses[0][0]}

    def get_current_operator_names(self):
        response = self.send_comm_get_response("AT+COPN")

        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+COPN: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)

            operators = []

            for parsed_response in parsed_responses:
                operators.append({"numeric": parsed_response[0], "alphanumeric": parsed_response[1]})

            return operators
    
    def get_signal_quality(self):
        response = self.send_comm_get_response("AT+CSQ")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CSQ: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"rssi": parsed_response[0], "ber": parsed_response[1]}
    
    def get_network_information(self):
        response = self.send_comm_get_response("AT+QNWINFO")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QNWINFO: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"act": parsed_response[0], "oper": parsed_response[1], "band": parsed_response[2], "channel": parsed_response[3]}
    
    def get_latest_time(self):
        response = self.send_comm_get_response("AT+QLTS")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QLTS: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"datetime": parsed_responses[0]}
    
    #---PACKET DATA---#
    def get_packet_service_status(self):
        response = self.send_comm_get_response("AT+CGATT?")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CGATT: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"state": int(parsed_response[0])}
    
    def set_packet_service_status(self, value):
        response = self.send_comm_get_response(f"AT+CGATT={value}")
        if(response['status_code'] == Status.OK):
            return True
        else:
            #Set failed
            return False
    
    def get_pdp_context(self):
        response = self.send_comm_get_response("AT+CGDCONT?")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CGDCONT: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"cid": parsed_response[0], "pdp_type": parsed_response[1], "apn": parsed_response[2], "pdp_address": parsed_response[3], "data_comp": parsed_response[4], "head_comp": parsed_response[5], "ipv4_address_allocation": parsed_response[6]}
    
    def set_pdp_context(self, cid=1, pdp_type="IPV4V6", apn="super"):
        response = self.send_comm_get_response(f'AT+CGDCONT={cid}, "{pdp_type}", "{apn}"')
        if(response['status_code'] == Status.OK):
            return True
        else:
            #Set failed
            return False
    
    def get_pdp_status(self):
        response = self.send_comm_get_response(f"AT+CGACT?")

        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CGACT: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)

            contexts = []

            for parsed_response in parsed_responses:
                contexts.append({"cid": int(parsed_response[0]), "state": int(parsed_response[1])})

            return contexts
    
    def set_pdp_status(self, cid, value):
        response = self.send_comm_get_response(f"AT+CGACT={value},{cid}")
        if(response['status_code'] == Status.OK):
            return True
        else:
            return False
    
    def get_pdp_address(self, cid=1):
        response = self.send_comm_get_response(f"AT+CGPADDR={cid}")
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CGPADDR: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {"cid": parsed_response[0], "pdp_address": parsed_response[1]}
    
    #---GNSS---#
    def get_gps_power_state(self):
        response = self.send_comm_get_response('AT+QGPS?')
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QGPS: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return bool(parsed_response[0])
    
    def set_gps_power_state(self, value):
        if(value == True):
            response = self.send_comm_get_response('AT+QGPS=1')
            if(response['status_code'] == Status.OK):
                return True
            else:
                #Failed set
                return False
        else:
            response = self.send_comm_get_response('AT+QGPSEND')
            if(response['status_code'] == Status.OK):
                return True
            else:
                #Failed set
                return False
        
    def get_position_information(self):
        response = self.send_comm_get_response('AT+QGPSLOC?')
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+CREG: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            return {
                "time": parsed_response[0],
                "latitude": parsed_response[1],
                "longitude": parsed_response[2],
                "hdop": parsed_response[3],
                "altitude": parsed_response[4],
                "fix": parsed_response[5],
                "course_over_ground": parsed_response[6],
                "speed_km": parsed_response[7],
                "speed_kn": parsed_response[8],
                "date": parsed_response[9],
                "satellites": parsed_response[10]
                }
    
    #---FILE---#
    def get_file_list(self, path="*"):
        """
        Function for getting file list
        """
        response = self.send_comm_get_response(f'AT+QFLST="{path}"')
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QFLST: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)

            files = [{'file_name': x[0].strip('"'), 'file_size': int(x[1])} for x in parsed_responses]
            return files

    def delete_file_from_modem(self, file_name):
        """
        Function for deleting file from modem UFS storage
        """

        response = self.send_comm_get_response(f'AT+QFDEL="{file_name}"')
        if(response['status_code'] == Status.OK):
            return True
        else:
            #Set failed
            return False

    def upload_file_to_modem(self, filename, file, timeout=5000):
        """
        Function for uploading file to modem
        """

        self.send_comm(f'AT+QFUPL="{filename}",{len(file)},{timeout}')
        #Wait for modem to respond with CONNECT
        logger.info("Waiting for CONNECT")
        
        #logger.info(f"Feeding watchdog")
        watchdog.feed()
        
        ready = self.wait_for_response(re.compile(r"^CONNECT$"))
        time.sleep(.1)
        #Send file contents
        self.send_comm(file)
        #Wait for confirmation of reciept of file contents from modem
        logger.info("Waiting for read confirmation")
        response = self.get_response()

        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QFUPL: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)
            parsed_response = parsed_responses[0]

            confirmation = {'upload_size': int(parsed_response[0]), 'checksum': parsed_response[1]}
            return True
        else:
            #Set failed
            return False

    #---MQTT---#
    def get_open_mqtt_sockets(self):
        
        response = self.send_comm_get_response(f'AT+QMTOPEN?')
        
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QMTOPEN: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)

            return [{'socket_id': parsed_response[0], 'hostname': parsed_response[1], 'port': int(parsed_response[2])} for parsed_response in parsed_responses]
        
        else:
            logger.info("Error")
    
    def get_open_mqtt_socket_ids(self):
        
        response = self.send_comm_get_response(f'AT+QMTOPEN?')
        
        if(response['status_code'] == Status.OK):
            pattern = re.compile(r"^\+QMTOPEN: (.*)$")
            parsed_responses = self.parse_response_data(response['data'], pattern)

            return [parsed_response[0] for parsed_response in parsed_responses]
        else:
            logger.info("Error")
            
    def create_mqtt_connection(self, client_id, hostname, port=8883, ssl_context=1):
        #Get lowest numerical available ID
        used_ids = self.get_open_mqtt_socket_ids()
        
        logger.info(f"Used IDs: {used_ids}")
        
        socket_id = None
        
        for i in range(0,6):
            if i not in used_ids:
                socket_id = i
                break
        
        if socket_id == None:
            logger.warning(f"Failed to create new MQTT socket, no available sockets")
            return None
        else:
            logger.info(f"Smallest available ID: {i}")
        
        socket = MQTT_Socket(self, client_id, hostname, port, socket_id)
        
        return socket