import alarm
import microcontroller
import supervisor
import time

if supervisor.runtime.safe_mode_reason == supervisor.SafeModeReason.BROWNOUT:
    time_alarm = alarm.time.TimeAlarm(monotonic_time = time.monotonic() + 360*60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
    
else:
    microcontroller.reset()