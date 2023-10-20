import sys
import socket
import json
import base64
import _thread
from machine import Pin, PWM
import utime
import network


# Pin de sensores
ECHO = Pin(27, Pin.IN)
TRIG = Pin(26, Pin.OUT)
SERVO_1 = Pin(17, Pin.OUT)
# Variables globales
server = socket.socket()
dataSensor = []

# ----------------------------------
# Clases
# ----------------------------------


class Sensor:
    def __init__(self, sensor, data):
        self.sensorName = sensor
        self.data = dict(data)

    def toJSON(self):
        jsonFormat = {
            "type": self.sensorName,
            "data": self.data,
            "time": utime.localtime()
        }
        return json.dumps(jsonFormat)

# ----------------------------------
# Funciones conectividad
# ----------------------------------


def connectServer():
    print("Connecting...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # wlan.connect('Alec Honor', "DarklinkA")
    wlan.connect('INFINITUM1B29_2.4', "3vq4v7vPsV")

    while not wlan.isconnected():
        pass

    print('Connect!, IP:', wlan.ifconfig()[0])
    print("Connecting to server...")
    sTmp = socket.socket()
    sTmp.setblocking(False)
    host = '192.168.174.38'
    port = 8080
    sTmp.connect((host, port))
    return sTmp


def sendData(dataSend):
    try:
        encodeData = base64.b64encode(dataSend.encode('utf-8'))
        server.send(encodeData)
    except OSError as e:
        if e.errno in (9, 104):
            print(f"\t▣ Data Failed Send! ->\t{e}")
            return False
    print("\t▣ Data Send!")


def reciveData():
    try:
        if (data := server.recv(1024)) is not None:
            data = base64.b64decode(data)
            data = json.loads(data)
            print("\t▣ Data Recive!")
            return data
        print("\t▣ Data is None!")
        return None
    except OSError as e:
        if e.errno in (9, 104):
            print(f"\t▣ Data Failed Recive! ->\t{e}")
        return None


def sensorUltrasonico():
    inicio = 0
    fin = 0

    TRIG.low()
    utime.sleep_us(2)

    TRIG.high()
    utime.sleep_us(10)

    TRIG.low()

    while ECHO.value() == 0:
        inicio = utime.ticks_us()
    while ECHO.value() == 1:
        fin = utime.ticks_us()

    output = Sensor("Ultrasonico", {"inicio": inicio, "fin": fin})
    return output.toJSON()

# ----------------------------------
# Funciones acciones
# ----------------------------------


def openDoor(servo: Pin):
    pwmServo = PWM(servo)
    pwmServo.freq(50)

    pwmServo.duty_u16(8000)
    utime.sleep(2)
    pwmServo.duty_u16(2000)
    return True
# ----------------------------------
# Funciones por hilos
# ----------------------------------


def bridgeServer(data):
    print(f"\t▣ {data} \n")
    # Mandar informacion de sensores
    if len(data) != 0:
        print("\t▣ Sending data...")
        for i, d in enumerate(data):
            status = sendData(d)
            print(f"\t▣ {i+1} Sensor: {d.sensor}\nStatus: {status}")
        data = []
    else:
        print("\t▣ No data to send!")

    # Recibir datos
    data = reciveData()
    if data is not None:
        print("\t▣ Action: ", data["function"])
        actions(data["function"], data["args"])


def getDataSensors(data: list):
    while True:
        data.append(sensorUltrasonico())
        # Los demas datos de otros sensores aqui
        utime.sleep(0.5)


def actions(strFunction: str, args: tuple = ()):
    actionsToDo = {
        "openDoor": openDoor
    }
    status = actionsToDo[strFunction](*args)
    print(f"\t◈ Status Action: {status}")


if __name__ == '__main__':
    print("Init program...")
    if (server := connectServer()) is None:
        print("Error in connect server!")
        sys.exit()

    _thread.start_new_thread(bridgeServer, (dataSensor,))
    getDataSensors(dataSensor)
