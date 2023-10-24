import sys
import socket
import json
import base64
import _thread
from machine import Pin, PWM
import utime
import network
# from mfrc522 import MFRC522

# ----------------------------------
# Pin de sensores
# ----------------------------------
ECHO = Pin(3, Pin.IN)
TRIG = Pin(4, Pin.OUT)
IR = Pin(2, Pin.IN)
# READER = MFRC522(spi_id=21, sck=20, miso=18, mosi=19, cs=17, rst=16)
SERVO_1 = Pin(22, Pin.OUT)
LED_1 = Pin(15, Pin.OUT)
LED_BICOLOR = (Pin(0, Pin.OUT), Pin(1, Pin.OUT))


# ----------------------------------
# Globales
# ----------------------------------
server = socket.socket()


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
    timeoutConnect = 0
    print("Connecting...")
    _thread.start_new_thread(initStatusLED, ())

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('RPI_Home', "Home@IoT")
    while not wlan.isconnected():
        timeoutConnect += 1
        utime.sleep(1)
        if timeoutConnect >= 30:
            raise TimeoutError

    _thread.exit()
    print('Connect!, IP:', wlan.ifconfig()[0])
    print("Connecting to server...")
    _thread.start_new_thread(initStatusLED, (3,))

    try:
        sTmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sTmp.connect(('200.10.0.6', 8080))
        _thread.exit()
        _thread.start_new_thread(initStatusLED, (1,))
        return sTmp
    except OSError as err:
        print(err)
        return None


def sendData(dataSend):
    try:
        encodeData = base64.b64encode(dataSend.encode('utf-8'))
        server.send(encodeData+"\n")
        print("\t▣ Data Send!")
        return True
    except OSError as err:
        if err.errno in (9, 104):
            print(f"\t▣ Data Failed Send! ->\t{err}")

            sys.exit()


def reciveData():
    try:
        data = server.recv(1024)
        if data is not None:
            data = base64.b64decode(data)
            data = json.loads(data)
            print("\t▣ Data Recive!")
            return data
        print("\t▣ Data is None!")
        return None
    except OSError as err:
        if err.errno in (9, 104):
            print(f"\t▣ Data Failed Recive! ->\t{err}")
            sys.exit()
        return None


# ----------------------------------
# Funciones sensores
# ----------------------------------
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


def sensorIR():
    IRValue: str = "False" if IR.value() == 1 else "True"
    output = Sensor("IR", {"status": IRValue})
    return output.toJSON()


# ----------------------------------
# Funciones acciones
# ----------------------------------
def openDoor(**kwargs):
    state = kwargs["state"]
    servo = globals()[kwargs["servo"]]
    pwmServo = PWM(servo)
    pwmServo.freq(50)

    if state is "ON":
        pwmServo.duty_u16(8000)
    else:
        pwmServo.duty_u16(2000)
    return True


def ledChange(**kwargs):
    state = kwargs["state"]
    led = globals()[kwargs["led"]]

    if state is "ON" and led.value() is 0:
        led.on()
        return True
    if state is "OFF" and led.value() is 1:
        led.off()
        return True
    return False

# ----------------------------------
# Funciones por hilos
# ----------------------------------


def serverWorker():
    while True:
        fn = reciveData()
        if fn is not None:
            print(f"\t▣ Action: {fn['function']} -> {fn['args']}")
            actions(fn["function"], fn["args"])


def getData_Send():
    data = []
    while True:
        # result = sensorUltrasonico()
        result = sensorIR()
        # Los demas datos de otros sensores aqui
        data.append(result) if result is not None else None

        # Manda los datos
        for i, d in enumerate(data):
            status = sendData(d)
            d = json.loads(d)
            print(
                f"\t ✦ {i+1} Sensor: {d["type"]}\n\t\tStatus: {status}", end="\n\n")
            utime.sleep(0.2)
        data = []


def actions(strFunction: str, kwargs: dict):
    actionsToDo = {
        "openDoor": openDoor,
        "ledChange": ledChange
    }
    status = actionsToDo[strFunction](**kwargs)
    print(f"\t\t ✩ Status Action: {status}")


def initStatusLED(mode: int = 0):
    if mode != 3:
        pwmLed = PWM(LED_BICOLOR[mode], freq=50)
        while True:
            for i in range(100):
                pwmLed.duty_u16(100*i)
                utime.sleep(0.01)
            for i in range(100):
                pwmLed.duty_u16(100*(100-i))
                utime.sleep(0.01)
    else:
        pwmLed1 = PWM(LED_BICOLOR[0], freq=50)
        pwmLed2 = PWM(LED_BICOLOR[1], freq=50)
        while True:
            for i in range(100):
                pwmLed1.duty_u16(100*i)
                pwmLed2.duty_u16(100*i)
                utime.sleep(0.01)
            for i in range(100):
                pwmLed1.duty_u16(100*(100-i))
                pwmLed2.duty_u16(100*(100-i))
                utime.sleep(0.01)


if __name__ == '__main__':
    print("Init program...")
    try:
        server = connectServer()
        utime.sleep(2)
        _thread.exit()
        LED_BICOLOR[1].on()
    except (TimeoutError, OSError) as e:
        print("Error! -> ", e)
        sys.exit()

    _thread.start_new_thread(serverWorker, ())
    getData_Send()