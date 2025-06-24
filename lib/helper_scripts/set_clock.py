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

# WiFi
print("Connecting to WiFi")
try:
    wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
    print(f"Successfully connected to WiFi with an IP address of: {wifi.radio.ipv4_address}")

except Exception as e:
    print(f"Failed to connect to WiFi: {e}")

pool = socketpool.SocketPool(wifi.radio)

# Sync time with NTP server
try:
    print(f"Syncing time with NTP server")
    ntp_instance = NTP.NTP(pool, server="pool.ntp.org", tz_offset=0)  # Set tz_offset as per your timezone
    rtc_instance = manager.devices['logicboard.rtc']
    rtc_instance.datetime = ntp_instance.datetime
    current_time = rtc_instance.datetime
    print(f"Successfully set device RTC to: {current_time.tm_hour:02d} :{current_time.tm_min:02d}:{current_time.tm_sec:02d}")
except Exception as e:
    print(f"Failed to sync time wtih NTP server: {e}")