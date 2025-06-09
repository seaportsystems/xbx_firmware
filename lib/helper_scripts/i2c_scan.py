'''
run this script to see all the devices recognized on the I2C bus
to run this script, go to the REPL and execute the following command:
from helper_scripts import i2c_scan
'''

import board
import time
from busio import I2C

print("Initializing I2C Bus")
i2c_bus = I2C(scl=board.GP13, sda=board.GP12)

locked = False
while(not(locked)):
    print("Waiting for bus lock")
    locked = i2c_bus.try_lock()

while True:    
    print("Bus locked successfully")
    print("Scanning bus")
    i2c_devices = i2c_bus.scan()

    print(f"{len(i2c_devices)} devices on the I2C bus")
    print("")
    print("Devices")
    print("-------")

    for d in i2c_devices:
        print(f"{hex(d)} | {d}")
        
    print("")
    time.sleep(1)