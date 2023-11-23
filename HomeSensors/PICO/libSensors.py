from machine import Pin, SPI
from os import uname
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
    MQ_SAMPLE_INTERVAL = const(100)
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


class MFRC522:

    DEBUG = False
    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

    PICC_ANTICOLL1 = 0x93
    PICC_ANTICOLL2 = 0x95
    PICC_ANTICOLL3 = 0x97

    def __init__(self, sck, mosi, miso, rst, cs, baudrate=1000000, spi_id=0):
        self.sck = Pin(sck, Pin.OUT)
        self.mosi = Pin(mosi, Pin.OUT)
        self.miso = Pin(miso)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)

        self.rst.value(0)
        self.cs.value(1)

        board = uname()[0]

        if board in ('WiPy', 'LoPy', 'FiPy'):
            self.spi = SPI(0)
            self.spi.init(SPI.MASTER, baudrate=1000000,
                          pins=(self.sck, self.mosi, self.miso))
        elif board in ('esp8266', 'esp32'):
            self.spi = SPI(baudrate=100000, polarity=0, phase=0,
                           sck=self.sck, mosi=self.mosi, miso=self.miso)
            self.spi.init()
        elif board == 'rp2':
            self.spi = SPI(spi_id, baudrate=baudrate,
                           sck=self.sck, mosi=self.mosi, miso=self.miso)
        else:
            raise RuntimeError("Unsupported platform")

        self.rst.value(1)
        self.init()

    def _wreg(self, reg, val):

        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.spi.write(b'%c' % int(0xff & val))
        self.cs.value(1)

    def _rreg(self, reg):

        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.spi.read(1)
        self.cs.value(1)

        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):
        recv = []
        bits = irq_en = wait_irq = n = 0
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break
        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR
        return stat, recv, bits

    def _crc(self, data):

        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def init(self):
        print("Init Sensor MFRC522")
        self.reset()
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def reset(self):
        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):
        print("Antena ON...")
        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])

        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self, anticolN):

        ser_chk = 0
        ser = [anticolN, 0x20]

        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def PcdSelect(self, serNum, anticolN):
        backData = []
        buf = []
        buf.append(anticolN)
        buf.append(0x70)
        # i = 0
        # xorsum=0;
        for i in serNum:
            buf.append(i)
        # while i<5:
        #    buf.append(serNum[i])
        #    i = i + 1
        pOut = self._crc(buf)
        buf.append(pOut[0])
        buf.append(pOut[1])
        (status, backData, backLen) = self._tocard(0x0C, buf)
        if (status == self.OK) and (backLen == 0x18):
            return 1
        else:
            return 0

    def SelectTag(self, uid):
        byte5 = 0

        # (status,puid)= self.anticoll(self.PICC_ANTICOLL1)
        # print("uid",uid,"puid",puid)
        for i in uid:
            byte5 = byte5 ^ i
        puid = uid + [byte5]

        if self.PcdSelect(puid, self.PICC_ANTICOLL1) == 0:
            return (self.ERR, [])
        return (self.OK, uid)

    def tohexstring(self, v):
        s = "["
        for i in v:
            if i != v[0]:
                s = s + ", "
            s = s + "0x{:02X}".format(i)
        s = s + "]"
        return s

    def SelectTagSN(self):
        valid_uid = []
        (status, uid) = self.anticoll(self.PICC_ANTICOLL1)
        # print("Select Tag 1:",self.tohexstring(uid))
        if status != self.OK:
            return (self.ERR, [])

        if self.DEBUG:
            print(f"anticol(1) {uid}")
        if self.PcdSelect(uid, self.PICC_ANTICOLL1) == 0:
            return (self.ERR, [])
        if self.DEBUG:
            print(f"pcdSelect(1) {uid}")

        # check if first byte is 0x88
        if uid[0] == 0x88:
            # ok we have another type of card
            valid_uid.extend(uid[1:4])
            (status, uid) = self.anticoll(self.PICC_ANTICOLL2)
            # print("Select Tag 2:",self.tohexstring(uid))
            if status != self.OK:
                return (self.ERR, [])
            if self.DEBUG:
                print(f"Anticol(2) {uid}")
            rtn = self.PcdSelect(uid, self.PICC_ANTICOLL2)
            if self.DEBUG:
                print(f"pcdSelect(2) return={rtn} uid={uid}")
            if rtn == 0:
                return (self.ERR, [])
            if self.DEBUG:
                print(f"PcdSelect2() {uid}")
            # now check again if uid[0] is 0x88
            if uid[0] == 0x88:
                valid_uid.extend(uid[1:4])
                (status, uid) = self.anticoll(self.PICC_ANTICOLL3)
                # print("Select Tag 3:",self.tohexstring(uid))
                if status != self.OK:
                    return (self.ERR, [])
                if self.DEBUG:
                    print(f"Anticol(3) {uid}")
                # if self.MFRC522_PcdSelect(uid, self.PICC_ANTICOLL3) == 0:
                    # return (self.ERR, [])
                if self.DEBUG:
                    print(f"PcdSelect(3) {uid}")
        valid_uid.extend(uid[0:5])
        # if we are here than the uid is ok
        # let's remove the last BYTE whic is the XOR sum

        return (self.OK, valid_uid[:len(valid_uid)-1])
        # return (self.OK , valid_uid)

    def auth(self, mode, addr, sect, ser):
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def authKeys(self, uid, addr, keyA=None, keyB=None):
        status = self.ERR
        if keyA is not None:
            status = self.auth(self.AUTHENT1A, addr, keyA, uid)
        elif keyB is not None:
            status = self.auth(self.AUTHENT1B, addr, keyB, uid)
        return status

    def stop_crypto1(self):
        self._cflags(0x08, 0x08)

    def read(self, addr):

        data = [0x30, addr]
        data += self._crc(data)
        (stat, recv, _) = self._tocard(0x0C, data)
        return stat, recv

    def write(self, addr, data):

        buf = [0xA0, addr]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)

        if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
            stat = self.ERR
        else:
            buf = []
            for i in range(16):
                buf.append(data[i])
            buf += self._crc(buf)
            (stat, recv, bits) = self._tocard(0x0C, buf)
            if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
                stat = self.ERR
        return stat

    def writeSectorBlock(self, uid, sector, block, data, keyA=None, keyB=None):
        absoluteBlock = sector * 4 + (block % 4)
        if absoluteBlock > 63:
            return self.ERR
        if len(data) != 16:
            return self.ERR
        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR:
            return self.write(absoluteBlock, data)
        return self.ERR

    def readSectorBlock(self, uid, sector, block, keyA=None, keyB=None):
        absoluteBlock = sector * 4 + (block % 4)
        if absoluteBlock > 63:
            return self.ERR, None
        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR:
            return self.read(absoluteBlock)
        return self.ERR, None

    def MFRC522_DumpClassic1K(self, uid, Start=0, End=64, keyA=None, keyB=None):
        status = None
        for absoluteBlock in range(Start, End):
            status = self.authKeys(uid, absoluteBlock, keyA, keyB)
            # Check if authenticated
            print("{:02d} S{:02d} B{:1d}: ".format(absoluteBlock,
                  absoluteBlock//4, absoluteBlock % 4), end="")
            if status == self.OK:
                status, block = self.read(absoluteBlock)
                if status == self.ERR:
                    break
                for value in block:
                    print("{:02X} ".format(value), end="")
                print("  ", end="")
                for value in block:
                    if (value > 0x20) and (value < 0x7f):
                        print(chr(value), end="")
                    else:
                        print('.', end="")
                print("")
            else:
                break
        if status == self.ERR:
            print("Authentication error")
            return self.ERR
        return self.OK


# ----------------------------------
# Recopilacion de datos de Sensores
# ----------------------------------
def gas(sensor: MQ2):
    return Sensor("Gas", {
        # "Smoke": sensor.readSmoke(),
        # "LPG": sensor.readLPG(),
        "Methane": sensor.readMethane(),
        # "Hydrogen": sensor.readHydrogen()
    })


def humedad(sensor):
    # print("Humedad: " + str(HUMEDAD.read_u16()))
    return Sensor("Humedad", {"valueAnalog": sensor.read_u16()})


def rfid(sensor):
    (stat, tag_type) = sensor.request(sensor.REQIDL)
    if stat == sensor.OK:
        (stat, uid) = sensor.SelectTagSN()
        if stat == sensor.OK:
            card = int.from_bytes(bytes(uid), "little", False)
            return Sensor("RFID", {"card": card})
    return Sensor("RFID", {"card": "null"})


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
