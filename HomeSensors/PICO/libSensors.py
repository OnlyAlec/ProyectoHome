from machine import ADC
from micropython import const
import utime
from math import exp, log


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


class BaseMQ(object):
    MQ_SAMPLE_TIMES = const(5)
    MQ_SAMPLE_INTERVAL = const(500)
    MQ_HEATING_PERIOD = const(60000)
    MQ_COOLING_PERIOD = const(90000)
    STRATEGY_FAST = const(1)
    STRATEGY_ACCURATE = const(2)

    def __init__(self, pinData, pinHeater=-1, boardResistance=10, baseVoltage=3.3, measuringStrategy=STRATEGY_ACCURATE):
        self._heater = False
        self._cooler = False
        self._ro = -1

        self._useSeparateHeater = False
        self._baseVoltage = baseVoltage

        self._lastMesurement = utime.ticks_ms()
        self._rsCache = None
        self.dataIsReliable = False
        self.pinData = ADC(pinData)
        self.measuringStrategy = measuringStrategy
        self._boardResistance = boardResistance
        if pinHeater != -1:
            self.useSeparateHeater = True
            self.pinHeater = Pin(pinHeater, Pin.OUTPUT)

    def getRoInCleanAir(self):
        raise NotImplementedError("Please Implement this method")

    def calibrate(self, ro=-1):
        if ro == -1:
            ro = 0
            print("Calibrating:")
            for i in range(0, self.MQ_SAMPLE_TIMES + 1):
                print("Step {0}".format(i))
                ro += self.__calculateResistance__(self.pinData.read_u16())
                utime.sleep_ms(self.MQ_SAMPLE_INTERVAL)
                pass
            ro = ro/(self.getRoInCleanAir() * self.MQ_SAMPLE_TIMES)
            pass
        self._ro = ro
        self._stateCalibrate = True

    def heaterPwrHigh(self):
        # digitalWrite(_pinHeater, HIGH)
        # _pinHeater(1)
        if self._useSeparateHeater:
            self._pinHeater.on()
            pass
        self._heater = True
        self._prMillis = utime.ticks_ms()

    def heaterPwrLow(self):
        # analogWrite(_pinHeater, 75)
        self._heater = True
        self._cooler = True
        self._prMillis = utime.ticks_ms()

    def heaterPwrOff(self):
        if self._useSeparateHeater:
            self._pinHeater.off()
            pass
        _pinHeater(0)
        self._heater = False

    def __calculateResistance__(self, rawAdc):
        vrl = rawAdc*(self._baseVoltage / 65535)
        rsAir = (self._baseVoltage - vrl)/vrl*self._boardResistance
        return rsAir

    def __readRs__(self):
        if self.measuringStrategy == self. STRATEGY_ACCURATE:
            rs = 0
            for i in range(0, self.MQ_SAMPLE_TIMES + 1):
                rs += self.__calculateResistance__(self.pinData.read_u16())
                utime.sleep_ms(self.MQ_SAMPLE_INTERVAL)

            rs = rs/self.MQ_SAMPLE_TIMES
            self._rsCache = rs
            self.dataIsReliable = True
            self._lastMesurement = utime.ticks_ms()
        else:
            rs = self.__calculateResistance__(self.pinData.read_u16())
            self.dataIsReliable = False
        return rs

    def readScaled(self, a, b):
        return exp((log(self.readRatio())-b)/a)

    def readRatio(self):
        return self.__readRs__()/self._ro

    def heatingCompleted(self):
        if (self._heater) and (not self._cooler) and (utime.ticks_diff(utime.ticks_ms(), self._prMillis) > self.MQ_HEATING_PERIOD):
            return True
        return False

    def coolanceCompleted(self):
        if (self._heater) and (self._cooler) and (utime.ticks_diff(utime.ticks_ms(), self._prMillis) > self.MQ_COOLING_PERIOD):
            return True
        return False

    def cycleHeat(self):
        self._heater = False
        self._cooler = False
        self.heaterPwrHigh()
        print("Heated sensor")

    # Use this to automatically bounce heating and cooling states
    def atHeatCycleEnd(self):
        if self.heatingCompleted():
            self.heaterPwrLow()
            print("Cool sensor")
            return False
        if self.coolanceCompleted():
            self.heaterPwrOff()
            return True
        return False


class MQ2(BaseMQ):
    MQ2_RO_BASE = float(9.83)

    def __init__(self, pinData, pinHeater=-1, boardResistance=10, baseVoltage=3.3, measuringStrategy=BaseMQ.STRATEGY_ACCURATE):
        super().__init__(pinData, pinHeater, boardResistance, baseVoltage, measuringStrategy)

    def readLPG(self):
        return self.readScaled(-0.45, 2.95)

    def readMethane(self):
        return self.readScaled(-0.38, 3.21)

    def readSmoke(self):
        return self.readScaled(-0.42, 3.54)

    def readHydrogen(self):
        return self.readScaled(-0.48, 3.32)

    def getRoInCleanAir(self):
        return self.MQ2_RO_BASE


# ----------------------------------
# Recopilacion de datos de Sensores
# ----------------------------------
def gas(sensor: MQ2):
    return Sensor("Gas", {
        "Smoke": sensor.readSmoke(),
        "LPG": sensor.readLPG(),
        "Methane": sensor.readMethane(),
        "Hydrogen": sensor.readHydrogen()
    })


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
