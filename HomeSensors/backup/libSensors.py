from machine import ADC
from micropython import const
import utime


class MQ2():
    MQ_SAMPLE_TIMES = const(5)
    MQ_CALIBRATION_INTERVAL = const(10)
    MQ_SAMPLE_INTERVAL = const(20)
    MQ2_RO_BASE = float(9.83)

    def __init__(self, pinData, boardResistance=10, baseVoltage=5.0):
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
            print(f"\t\t -> Step {i}")
            ro += self.__calculateResistance__(self.pinData.read_u16())
            utime.sleep_ms(self.MQ_CALIBRATION_INTERVAL)
        ro = ro/ (self.MQ2_RO_BASE * self.MQ_SAMPLE_TIMES)

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
