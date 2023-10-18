import socket
import json
import base64
from machine import Pin
import utime
import network

# Variables globales
ECHO = Pin(27, Pin.IN)
TRIG = Pin(26, Pin.OUT)
HEADER_BYTE = 0xAA
TERMINATOR_BYTE = 0xBB


def connectServer():
    print("Connecting...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('INFINITUM1B29_2.4', '3vq4v7vPsV')

    while not wlan.isconnected():
        pass

    print('Connect!, IP:', wlan.ifconfig()[0])

    sTmp = socket.socket()
    host = '192.168.1.204'
    port = 45871
    sTmp.connect((host, port))
    return sTmp


def getInfo():
    TRIG.low()
    utime.sleep_us(2)

    TRIG.high()
    utime.sleep_us(10)

    TRIG.low()

    while ECHO.value() == 0:
        inicio = utime.ticks_us()
    while ECHO.value() == 1:
        fin = utime.ticks_us()

    return inicio, fin


def sendData(dataSend):
    global timeout
    try:
        dataSend = json.dumps(dataSend)
        encodeData = base64.b64encode(dataSend.encode('utf-8'))
        server.send(encodeData)
    except OSError as e:
        if e.errno in (9, 104):
            timeout = True
        print(f"Data Failed Send! ->\t{e}")
        return None
    print("Data Send!")


# Main
print("Init program...")
server = connectServer()
timeout = False

while timeout is not True:
    print("\nGetting data...")
    data = getInfo()
    print("Data:", data)
    if data is not None:
        sendData(data)
        utime.sleep(5)
    else:
        utime.sleep(1)
