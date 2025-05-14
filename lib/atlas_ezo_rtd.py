import time

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

try:
    from typing import Iterable, Optional, Tuple
    from typing_extensions import Literal
    from circuitpython_typing import ReadableBuffer
    from busio import I2C
except ImportError:
    pass

EZO_EC_I2CADDR_DEFAULT = const(0x66)

class EZO_RTD:

    def __init__(self, i2c_bus: I2C, address: int = EZO_EC_I2CADDR_DEFAULT) -> None:
        self.i2c_device = I2CDevice(i2c_bus, address)

        self._buf = bytearray(40)
    
    @property
    def calibration(self):
        try:
            return self._parse_message(self._write_then_read('Cal,?', 300, 8))
        
        except:
            raise ConnectionError

    def find(self) -> None:
        try:
            self._write_then_read("Find", response_len=2)
        except:
            raise ConnectionError

    def device_info(self):
        try:
            return self._parse_message(self._write_then_read('i', 300, 42))
        
        except:
            raise ConnectionError
        
    @property
    def led(self) -> bool:
        try:
            response = self._write_then_read("L,?", delay=300, response_len=6)
            
            parsed_message = self._parse_message(response)

            return parsed_message[3]
        except:
            raise ConnectionError
        
    @led.setter
    def led(self, status) -> None:
        try:
            if(status not in (True, False, 1, 0)):
                raise ValueError("Status must be bool or resolve to bool")
            
            if(status):
                command = "L,1"
            else:
                command = "L,0"

            self._write_then_read(command, response_len=3)
        except:
            raise ConnectionError
    
    @property
    def units(self):
        try:
            response = self._write_then_read("S,?", delay=300, response_len=6)
            
            parsed_message = self._parse_message(response)

            return parsed_message[3]
        except:
            raise ConnectionError
        
    @units.setter
    def units(self, unit):
        unit = unit.lower()
        try:
            if(unit not in ("s", "k", "f")):
                raise ValueError("Status must be 's', 'k', or 'f'")

            command = f"S,{unit}"
            self._write_then_read(command, response_len=3)
        except:
            raise ConnectionError

    def get_reading(self):
        try:
            readings = self._parse_message(self._write_then_read('R', 600, 42))

            readings = readings.split(',')
            return readings
        
        except:
            raise ConnectionError
    
    @property
    def T(self):
        try:
            return self.get_reading()[0]
        
        except:
            raise ConnectionError


    def sleep(self):
        try:
            with self.i2c_device as i2c:
                i2c.write(bytearray("Sleep".encode("utf-8")))
        
        except:
            raise ConnectionError
        
    def status(self):
        try:
            return self._parse_message(self._write_then_read('Status', 300, 16))
        
        except:
            raise ConnectionError
        
    def _write_then_read(self, command, delay=300, response_len=40):
        output = bytearray(response_len)
        with self.i2c_device as i2c:
            i2c.write(bytearray(command.encode("utf-8")))
            time.sleep(delay/1000)
            i2c.readinto(output)

        return output
    
    def _parse_message(self, raw_message):
        start = raw_message.find(b'\x01')  # Find the start of the message
        end = raw_message.find(b'\x00')  # Find the end of the message

        if start != -1 and end != -1:
            message = raw_message[start + 1:end]  # Extract the message between start and end
            decoded_message = ''.join(chr(byte) for byte in message)  # Convert ASCII codes to characters
            return decoded_message
        else:
            return None  # No valid message found in the data