from machine import ADC
import utime
from math import exp, log


class MQ2():
    MQ_SAMPLE_TIMES = const(5)
    MQ_CALIBRATION_INTERVAL = const(3000)
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
            print(f"\t -> Step {i}")
            ro += self.__calculateResistance__(self.pinData.read_u16())
            utime.sleep_ms(self.MQ_CALIBRATION_INTERVAL)
        val = ro / self.MQ_SAMPLE_TIMES
        ro = val / self.MQ2_RO_BASE
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


def sGas(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    ro = kwargs["ro"]
    # ^LPG, Methane, Smoke, Hydrogen
    listValues = [(-0.45, 2.95), (-0.38, 3.21), (-0.42, 3.54), (-0.48, 3.32)]
    results = []
    for (a, b) in listValues:
        ratio = vAnalog/ro
        results.append(exp(log(ratio-b)/a))

    print('\t\t◈  Gas:',
          f'LPG: {results[0]},',
          f'Methane: {results[1]},',
          f'Smoke: {results[2]},',
          f'Hydrogen: {results[3]}', sep='\n\t\t\t'
          )


def sLuz(**kwargs):
    maxDark = 65535
    minLight = 0
    vAnalog = kwargs["valueAnalog"]

    porcentaje = ((vAnalog - minLight) / (maxDark - minLight)) * 100
    porcentaje = 100 - porcentaje
    porcentaje = max(0, min(100, porcentaje))

    print(f'\t\t◈  Luz: {porcentaje}')


LUZ = ADC(26)
GAS = MQ2(27)

GAS.calibrate()
while True:
    l = LUZ.read_u16()
    g = GAS.__readRs__()

    print(f"Luz: {l}")
    print(f"Gas: {g}")

    sGas(valueAnalog=g, ro=GAS.ro)
    sLuz(valueAnalog=l)
    utime.sleep(1)
