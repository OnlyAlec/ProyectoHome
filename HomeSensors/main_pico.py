import sys
import socket
import _thread
from machine import Pin, PWM, ADC
import utime
import network
# from mfrc522 import MFRC522
import libConnectPico

# ----------------------------------
# Pin de sensores
# ----------------------------------
ECHO = Pin(3, Pin.IN)
TRIG = Pin(4, Pin.OUT)
IR = Pin(28, Pin.IN)
# READER = MFRC522(spi_id=21, sck=20, miso=18, mosi=19, cs=17, rst=16)
SERVO_1 = Pin(22, Pin.OUT)
LED_1 = Pin(15, Pin.OUT)
LED_BICOLOR = (Pin(0, Pin.OUT), Pin(1, Pin.OUT))
TEMP = ADC(26)


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

    def toDict(self):
        return {
            "sensorName": self.sensorName,
            "data": self.data,
            "time": utime.localtime()
        }


# ----------------------------------
# Funciones conectividad
# ----------------------------------
def connectServer(host, port):
    print("Connecting...", end=" ")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('RPI_Home', "Home@IoT")
    # wlan.connect('Alec Honor', "DarklinkA")
    try:
        initStatusLED(wlan)
    except OSError as err:
        print("\tFailed! -> ", err)
        sys.exit()

    print('\tOK! -> IP:', wlan.ifconfig()[0])

    s = libConnectPico.initConnectRPI(host, port)
    return s


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

    return Sensor("Ultrasonico", {"inicio": inicio, "fin": fin})


def sensorIR():
    irValue: str = "False" if IR.value() == 1 else "True"
    Sensor("IR", {"status": irValue})
    return Sensor("IR", {"status": irValue})


def sensorTemp():
    utime.sleep(2)
    valueAnalog = TEMP.read_u16()
    return Sensor("Temperatura", {"valueAnalog": valueAnalog})


# ----------------------------------
# Funciones acciones
# ----------------------------------
def openDoor(**kwargs):
    state = kwargs["state"]
    servo = globals()[kwargs["servo"]]
    pwmServo = PWM(servo)
    pwmServo.freq(50)

    if state == "ON":
        pwmServo.duty_u16(8000)
    else:
        pwmServo.duty_u16(2000)
    return True


def ledChange(**kwargs):
    state = kwargs["state"]
    led = globals()[kwargs["led"]]

    if state == "ON" and led.value() == 0:
        led.on()
        return True
    if state == "OFF" and led.value() == 1:
        led.off()
        return True
    return False


def actions(strFunction: str, kwargs: dict):
    actionsToDo = {
        "openDoor": openDoor,
        "ledChange": ledChange
    }
    status = actionsToDo[strFunction](**kwargs)
    print(f"\t\t # Status Action: {status}")


# ----------------------------------
# Funciones para datos
# ----------------------------------
def recolectData():
    data = []
    while True:
        # data.append(sensorUltrasonico())
        data.append(sensorIR())
        # Los demas datos de otros sensores aqui

        d: Sensor
        for i, d in enumerate(data):
            print(f"■ {i+1} Sensor: {d.sensorName}", end="\n\n")
            libConnectPico.senderWorker(server, d.toDict())
        data = []
        utime.sleep(1.5)


def initStatusLED(wlan, mode: int = 0):
    timeoutConnect = 0
    pwmLed = PWM(LED_BICOLOR[mode], freq=50)
    if mode == 0:
        while not wlan.isconnected():
            timeoutConnect += 1
            if timeoutConnect > 30:
                raise OSError("Timeout connect!")
            for i in range(100):
                pwmLed.duty_u16(100*i)
                utime.sleep(0.01)
            for i in range(100):
                pwmLed.duty_u16(100*(100-i))
                utime.sleep(0.01)
        pwmLed.deinit()
        LED_BICOLOR[0].init(mode=Pin.OUT)
        LED_BICOLOR[1].init(mode=Pin.OUT)
        LED_BICOLOR[0].value(1)
        LED_BICOLOR[1].value(1)
    else:
        for i in range(100):
            pwmLed.duty_u16(100*i)
            utime.sleep(0.01)
        for i in range(100):
            pwmLed.duty_u16(100*(100-i))
            utime.sleep(0.01)
        for i in range(100):
            pwmLed.duty_u16(100*i)
            utime.sleep(0.01)
        LED_BICOLOR[0].init(mode=Pin.OUT)
        LED_BICOLOR[1].init(mode=Pin.OUT)
        LED_BICOLOR[0].value(0)
        LED_BICOLOR[1].value(1)


# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    print("Init program...")
    LED_BICOLOR[1].value(0)
    LED_BICOLOR[0].value(0)
    try:
        server = connectServer(host="200.10.0.6", port=8080)
        # server = connectServer(host="192.168.191.1", port=8080)
        initStatusLED(None, 1)
    except (OSError) as e:
        print("Error! -> ", e)
        sys.exit()

    _thread.start_new_thread(libConnectPico.listenerWorker, (server,))
    recolectData()
