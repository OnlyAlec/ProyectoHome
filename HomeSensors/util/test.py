from machine import Pin
import utime


LED_JARDIN = Pin(2, Pin.OUT)


while True:
    LED_JARDIN.value(1)
    utime.sleep_ms(100)
    LED_JARDIN.value(0)
    utime.sleep_ms(100)
