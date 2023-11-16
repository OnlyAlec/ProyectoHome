from test import MQ2
import utime

pin = 27

sensor = MQ2(pinData=pin, baseVoltage=3.3)

print("Calibrating")
sensor.calibrate()
print("Calibration completed")
print("Base resistance:{0}".format(sensor._ro))

while True:
    print("Smoke: {:.1f}".format(sensor.readSmoke())+" - ", end="")
    print("LPG: {:.1f}".format(sensor.readLPG())+" - ", end="")
    print("Methane: {:.1f}".format(sensor.readMethane())+" - ", end="")
    print("Hydrogen: {:.1f}".format(sensor.readHydrogen()))
    utime.sleep(0.5)
