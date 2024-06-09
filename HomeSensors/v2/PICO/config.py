"""Librerias"""
from machine import Pin, PWM, ADC
from libSensors import MQ2, MFRC522

# JARDIN ---------------------------
PIN_JC_LED = Pin(2, Pin.OUT)
PIN_JT_LED = Pin(4, Pin.OUT)
PIN_JSL = ADC(26)
PIN_JH = ADC(28)

# COCINA ---------------------------
PIN_C_LED = Pin(7, Pin.OUT)
PIN_C_BUZZER = Pin(6, Pin.OUT)
PIN_CG = MQ2(pinData=27, baseVoltage=3.3)

# HABITACION ---------------------------
PIN_H_LED = Pin(9, Pin.OUT)
PIN_H_SERVO = Pin(8, Pin.OUT)
PIN_HT = ADC(4)

# GARAGE ---------------------------
PIN_G_LED = Pin(10, Pin.OUT)
PIN_G_SERVO = Pin(11, Pin.OUT)
PIN_G_BUZZER = Pin(12, Pin.OUT)

# ENTRADA ---------------------------
PIN_E_LED = Pin(15, Pin.OUT)
PIN_E_BUZZER = Pin(14, Pin.OUT)
PIN_EIR = Pin(13, Pin.IN)
PIN_ERFID = MFRC522(spi_id=0, sck=18, cs=17, mosi=19, miso=16, rst=20)
