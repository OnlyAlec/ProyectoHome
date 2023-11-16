import sys
import socket
import _thread
from machine import Pin, PWM, ADC
import utime
import network
# from mfrc522 import MFRC522

import libConnectPico
from libSensors import MQ2

# ----------------------------------
# Pin de sensores
# ----------------------------------
# JARDIN ---------------------------
LED_JARDIN = Pin(4, Pin.OUT)
LUZ = Pin(5, Pin.IN)
HUMEDAD = ADC(28)

# COCINA ---------------------------
BUZZER_COCINA = Pin(6, Pin.OUT)
LED_COCINA = Pin(7, Pin.OUT)
GAS = MQ2(27)


# HABITACION ---------------------------
SERVO_HABITACION = Pin(8, Pin.OUT)
PWM_SERVO_HABITACION = PWM(SERVO_HABITACION)
LED_HABITACION = Pin(9, Pin.OUT)
TEMP = ADC(26)

# GARAGE ---------------------------
LED_GAAAGE = Pin(10, Pin.OUT)
SERVO_GARAGE = Pin(11, Pin.OUT)
PWM_SERVO_GARAGE = PWM(SERVO_GARAGE)


# ENTRADA ---------------------------
IR = Pin(13, Pin.IN)
BUZZER_ENTRADA = Pin(14, Pin.OUT)
LED_ENTRADA = Pin(15, Pin.OUT)
# Checar lib
RFID = [Pin(16, Pin.IN), Pin(17, Pin.IN), Pin(18, Pin.IN),
        Pin(19, Pin.IN), Pin(20, Pin.IN), Pin(21, Pin.IN)]

# OTROS ---------------------------
LED_BICOLOR = (Pin(0, Pin.OUT), Pin(1, Pin.OUT))  # Listo

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
def ledAction(led, state):
    if state == "ON":
        led.value(1)
    else:
        led.value(0)


def sensorGas():
    read = GAS.__readRs__()
    # print("Gas: " + str(read))
    return Sensor("Gas", {"valueAnalog": read, "ro": GAS.ro})


def sensorHumedad():
    # print("Humedad: " + str(HUMEDAD.read_u16()))
    return Sensor("Humedad", {"valueAnalog": HUMEDAD.read_u16()})


def sensorRFID():
    #! TODO: Checar la libreria
    print("Libreria")


def sensorLuz():
    light = "False" if LUZ.value() == 1 else "True"
    # print("Luz: " + light)
    return Sensor("Luz", {"status": light})


def sensorIR():
    irValue: str = "False" if IR.value() == 1 else "True"
    # print("IR: " + irValue)
    return Sensor("IR", {"status": irValue})


def sensorTemp():
    valueAnalog = TEMP.read_u16()
    # print("Temperatura: " + str(valueAnalog))
    return Sensor("Temperatura", {"valueAnalog": valueAnalog})


# ----------------------------------
# Funciones acciones
# ----------------------------------
def ledChange(**kwargs):
    state = kwargs["state"]
    led = globals()[kwargs["led"]]
    print(f"\t\t # LED: {led} -> {state}")
    if state == "ON" and led.value() == 0:
        led.on()
        return True
    if state == "OFF" and led.value() == 1:
        led.off()
        return True
    return False


def servoAction(**kwargs):
    state = kwargs["state"]
    servo = globals()[kwargs["servo"]]
    pwmServo = PWM(servo)
    pwmServo.freq(50)

    if state == "ON":
        pwmServo.duty_u16(8000)
    else:
        pwmServo.duty_u16(2000)
    return True


def buzzerAction(**kwargs):
    buzzer = globals()[kwargs["servo"]]
    state = kwargs["state"]
    time = kwargs.get("time")

    if state == "ON":
        buzzer.on()
        utime.sleep(time)
        buzzer.off()
    else:
        buzzer.off()


def actions(strFunction: str, kwargs: dict):
    actionsToDo = {
        "ledChange": ledChange,
        "servoAction": servoAction,
        "buzzerAction": buzzerAction
    }
    try:
        status = actionsToDo[strFunction](**kwargs)
        print(f"\t\t # Status Action: {status}")
    except (Exception, KeyError):
        print(f"\t\t # Function: {strFunction} not found!")


# ----------------------------------
# Funciones para datos
# ----------------------------------
def recolectData():
    data = []
    i=0
    while True:
        data.append(sensorLuz().toDict())
        data.append(sensorHumedad().toDict())
        data.append(sensorIR().toDict())
        data.append(sensorTemp().toDict())
        data.append(sensorGas().toDict())
        # data.append(sensorRFID())

        print(f"{i} Preparing data...")
        libConnectPico.senderWorker(server, data)
        i+=1
        # d: Sensor
        # for i, d in enumerate(data):
        #     print(f"■ {i+1} Sensor: {d.sensorName}")
        #     libConnectPico.senderWorker(server, d.toDict())
        data = []
        utime.sleep_ms(2000)


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
    GAS.calibrate()

    try:
        server = connectServer(host="200.10.0.11", port=8080)
        initStatusLED(None, 1)
    except (OSError) as e:
        LED_BICOLOR[1].value(0)
        LED_BICOLOR[0].value(0)
        print("Error! -> ", e)
        sys.exit()

    _thread.start_new_thread(libConnectPico.listenerWorker, (server,))
    recolectData()
