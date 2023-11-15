from machine import ADC
from micropython import const
import utime


# ----------------------------------
# Clases de sensores
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


class MQ2():
    MQ_SAMPLE_TIMES = const(5)
    MQ_CALIBRATION_INTERVAL = const(3000)
    MQ_SAMPLE_INTERVAL = const(20)
    MQ2_RO_BASE = float(9.83)

    def __init__(self, pinData, boardResistance=10, baseVoltage=3.3):
        self.pinData = ADC(pinData)
        self._boardResistance = boardResistance
        self._baseVoltage = baseVoltage

        self.stateCalibrate = False
        self.ro = -1
        self._rsCache = None

    def calibrate(self):
        ro = 0
        self.stateCalibrate = True
        print("\n+ Calibrating Gas Sensor:")
        for i in range(0, self.MQ_SAMPLE_TIMES + 1):
            print(f"\t -> Step {i}")
            ro += self.__calculateResistance__(self.pinData.read_u16())
            utime.sleep_ms(self.MQ_CALIBRATION_INTERVAL)

        ro = ro / (self.MQ2_RO_BASE * self.MQ_SAMPLE_TIMES)
        self.ro = ro
        print(" + Calibration completed")
        print(f"\t = Base resistance:{self.ro}")

    def __calculateResistance__(self, rawAdc):
        vrl = rawAdc*(self._baseVoltage / 65535)
        rsAir = (self._baseVoltage - vrl)/vrl*self._boardResistance
        return rsAir

    def __readRs__(self):
        rs = 0
        for i in range(0, self.MQ_SAMPLE_TIMES + 1):
            rs += self.__calculateResistance__(self.pinData.read_u16())
            utime.sleep_ms(self.MQ_SAMPLE_INTERVAL)

        rs = rs/self.MQ_SAMPLE_TIMES
        self._rsCache = rs
        return rs


# ----------------------------------
# Recopilacion de datos de Sensores
# ----------------------------------
def gas(sensor: MQ2):
    read = sensor.__readRs__()
    # print("Gas: " + str(read))
    return Sensor("Gas", {"valueAnalog": read, "ro": sensor.ro})


def humedad(sensor):
    # print("Humedad: " + str(HUMEDAD.read_u16()))
    return Sensor("Humedad", {"valueAnalog": sensor.read_u16()})


def rfid(sensor):
    #! TODO: Checar la libreria
    print("Libreria")


def luz(sensor):
    # print("Luz: " + sensor.read_u16())
    return Sensor("Luz", {"valueAnalog": sensor.read_u16()})


def ir(sensor):
    irValue: str = "False" if sensor.value() == 1 else "True"
    # print("IR: " + irValue)
    return Sensor("IR", {"status": irValue})


def temp(sensor):
    valueAnalog = sensor.read_u16()
    # print("Temperatura: " + str(valueAnalog))
    return Sensor("Temperatura", {"valueAnalog": valueAnalog})
