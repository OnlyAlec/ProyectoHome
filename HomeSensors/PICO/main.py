import sys
import _thread

from machine import Pin, PWM
import utime
import network
from micropython import const

import libConnect as libPICO
import libSensors as sensorFn
import libActions as action
import config

# OTROS ---------------------------
LED_BICOLOR = (Pin(0, Pin.OUT), Pin(1, Pin.OUT))
EVENT_READ = const(0)
EVENT_WRITE = const(1)


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

    s = libPICO.initConnectRPI(host, port)
    return s


def initStatusLED(wlan, mode: int = 0):
    timeoutConnect = 0
    pwmLed = PWM(LED_BICOLOR[mode], freq=50)
    if mode == 0:
        while not wlan.isconnected():
            timeoutConnect += 1
            if timeoutConnect > 30:
                raise OSError("Timeout connect!")
            for count in range(100):
                pwmLed.duty_u16(100*count)
                utime.sleep(0.01)
            for count in range(100):
                pwmLed.duty_u16(100*(100-count))
                utime.sleep(0.01)
        pwmLed.deinit()
        LED_BICOLOR[0].init(mode=Pin.OUT)
        LED_BICOLOR[1].init(mode=Pin.OUT)
        LED_BICOLOR[0].value(1)
        LED_BICOLOR[1].value(1)
    else:
        for count in range(100):
            pwmLed.duty_u16(100*count)
            utime.sleep(0.01)
        for count in range(100):
            pwmLed.duty_u16(100*(100-count))
            utime.sleep(0.01)
        for count in range(100):
            pwmLed.duty_u16(100*count)
            utime.sleep(0.01)
        LED_BICOLOR[0].init(mode=Pin.OUT)
        LED_BICOLOR[1].init(mode=Pin.OUT)
        LED_BICOLOR[0].value(0)
        LED_BICOLOR[1].value(1)


# ----------------------------------
# Thread acciones
# ----------------------------------
def actionWorker(queue: dict):
    index = 0
    actionsToDo = {
        "ledChange": action.ledChange,
        "servoAction": action.servoAction,
        "buzzerAction": action.buzzerAction
    }
    while True:
        if not queue:
            utime.sleep(0.5)
            continue
        try:
            dictActions: dict = queue[index]
        except IndexError:
            utime.sleep(0.5)
            continue

        print("!!! Action Worker: Processing...")
        for sensor, accionPico in dictActions.items():
            if not isinstance(accionPico, list):
                accionPico = [accionPico]

            for simpleAction in accionPico:
                name = simpleAction["function"]
                kwargs = simpleAction["args"]
                if name not in actionsToDo:
                    print(f"\t\t # Function: {name} not found!\n\n name: {
                          name} -> kwargs: kwargs")
                    continue
                statusAction = actionsToDo[name](**kwargs)
                print(f"\t   -> Success? : {statusAction}")
        print("!!! Action Complete!")
        queue.pop(index)
        index += 1


# ----------------------------------
# Funciones para datos
# ----------------------------------
def recolectData():
    dataRecolect = []
    dataRecolect.append(sensorFn.luz(getattr(config, "LUZ")).toDict())
    dataRecolect.append(sensorFn.humedad(getattr(config, "HUMEDAD")).toDict())
    dataRecolect.append(sensorFn.ir(getattr(config, "IR")).toDict())
    dataRecolect.append(sensorFn.temp(getattr(config, "TEMP")).toDict())
    dataRecolect.append(sensorFn.gas(getattr(config, "GAS")).toDict())
    dataRecolect.append(sensorFn.rfid(getattr(config, "RFID")).toDict())
    return dataRecolect


# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    countPackage = 0
    mask = 1
    queueActions = []

    print("Init program...")
    LED_BICOLOR[1].value(0)
    LED_BICOLOR[0].value(1)
    getattr(config, "GAS").calibrate()

    try:
        server = connectServer(host="200.10.0.18", port=8080)
        # server = connectServer(host="200.10.0.15", port=8080)
        # server = connectServer(host="192.168.151.1", port=8080)
        initStatusLED(None, 1)
    except (OSError) as e:
        LED_BICOLOR[1].value(0)
        LED_BICOLOR[0].value(0)
        print("Error! -> ", e)
        sys.exit()

    _thread.start_new_thread(actionWorker, (queueActions,))
    conn = libPICO.senderListener(server, queueActions)

    conn.processEvents()
    while True:
        print("Recollect Data...")
        data = recolectData()
        print(f"{countPackage} || Preparing data...")
        conn.setData(data)
        for i in range(2):
            status = conn.processEvents()
            if status is False:
                print("Main: Quitting...")
                sys.exit()
            conn.wipe()
            utime.sleep_ms(500)
        countPackage += 1
