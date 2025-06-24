import adafruit_ntp as NTP
import boards
import os
import rtc
import socketpool
import ssl
import sys
import time
import wifi

from services.device_manager import manager

# GPS
gps = manager.devices['attitudeboard.gps']

# Wait for signal fix
has_fix = False

while not has_fix:
    fix = gps.base_device.fix_quality
    
    if fix > 0:
        has_fix = True
        
for _ in range(15):  # drain a few messages per loop
    gps.base_device.update()
    
last_gps_time = gps.base_device.datetime

got_new_time = False

latest_gps_time = None

while not got_new_time:
    gps.base_device.update()
    
    new_time = gps.base_device.datetime
    
    if new_time != last_gps_time:
        got_new_time = True
        latest_gps_time = new_time
   
rtc_instance = manager.devices['logicboard.rtc']
rtc_instance.datetime = latest_gps_time
current_time = rtc_instance.datetime
print(f"Successfully set device RTC to: {current_time.tm_year:04d}{current_time.tm_mon:02d}{current_time.tm_mday:02d}{current_time.tm_hour:02d} {current_time.tm_min:02d}:{current_time.tm_sec:02d}")