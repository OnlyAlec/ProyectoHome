"""Librerias."""
from machine import Pin, PWM, ADC
from libSensors import MQ2, MFRC522

"""Variables globales."""
# JARDIN ---------------------------
LED_JARDIN = Pin(2, Pin.OUT)
LED_JARDIN_LUZ = Pin(4, Pin.OUT)
LUZ = ADC(26)
HUMEDAD = ADC(28)

# COCINA ---------------------------
BUZZER_COCINA = Pin(6, Pin.OUT)
LED_COCINA = Pin(7, Pin.OUT)
GAS = MQ2(pinData=27, baseVoltage=3.3)

# HABITACION ---------------------------
SERVO_HABITACION = Pin(8, Pin.OUT)
LED_HABITACION = Pin(9, Pin.OUT)
TEMP = ADC(4)

# GARAGE ---------------------------
LED_GARAGE = Pin(10, Pin.OUT)
SERVO_GARAGE = Pin(11, Pin.OUT)
BUZZER_GARAGE = Pin(12, Pin.OUT)

# ENTRADA ---------------------------
IR = Pin(13, Pin.IN)
BUZZER_ENTRADA = Pin(14, Pin.OUT)
LED_ENTRADA = Pin(15, Pin.OUT)
RFID = MFRC522(spi_id=0, sck=18, cs=17, mosi=19, miso=16, rst=20)
