from os import uname
from math import exp, log
from machine import Pin, SPI, ADC, PWM
from micropython import const
from time import sleep
import utime
import config

sList = {}
cList = {}


# ----------------------------------
# Clases de sensores
# ----------------------------------
class Sensor:
    """
    Clase para representar un sensor.

    Attributes:
        nameSensor: Nombre del sensor
        pin: El pin puede ser un objeto Pin, ADC, PWM, etc.
        data: Diccionario con los datos del sensor

    Methods:
        toDict:
            Devuelve un diccionario con los datos del sensor
    """

    def __init__(self, name: str, pin, data=None):
        self.nameSensor = name
        self.pin = pin
        self.data: list = list(data) if data else []

    def toDict(self):
        """
        Devuelve un diccionario con los datos del sensor.
        """
        return {
            "sensorName": self.nameSensor,
            "data": self.data,
            "time": utime.localtime()
        }

    def calibrate(self):
        """
        Calibra el sensor.
        """
        typeSensor = type(self.pin)
        if typeSensor == ADC:
            res = self.pin.read_u16()
            if res > 0:
                return True
            return False
        if typeSensor == MQ2:
            self.pin.calibrate()
            return True
        if typeSensor == MFRC522:
            self.pin.init()
            return True

        return False

    def read(self):
        """
        Lee el sensor.
        """
        typeSensor = type(self.pin)
        if typeSensor == Pin:
            self.data.append(False if self.pin.value() == 1 else True)
        elif typeSensor == ADC:
            self.data.append(self.pin.read_u16())
        elif typeSensor == MQ2:
            self.data.append(self.pin.readSmoke(),)
            self.data.append(self.pin.readLPG(),)
            self.data.append(self.pin.readMethane(),)
            self.data.append(self.pin.readHydrogen())
        elif typeSensor == MFRC522:
            (stat, tag_type) = self.pin.request(self.pin.REQIDL)
            if stat == self.pin.OK:
                (stat, uid) = self.pin.SelectTagSN()
                if stat == self.pin.OK:
                    card = int.from_bytes(bytes(uid), "little", signed=False)
                    self.data.append(card)

        return self.data


class Led(Sensor):
    """
    Clase para representar un LED.

    Attributes:
        pin: Pin del LED
        state: Estado del LED

    Methods:
        on:
            Enciende el LED
        off:
            Apaga el LED
        toggle:
            Cambia el estado del LED
    """

    def __init__(self, name, pin):
        super().__init__(name, pin)
        self.state = False

    def on(self):
        """
        Enciende el LED.
        """
        self.pin.on()
        self.state = True

    def off(self):
        """
        Apaga el LED.
        """
        self.pin.off()
        self.state = False

    def toggle(self):
        """
        Cambia el estado del LED.
        """
        self.state = not self.state
        self.pin.value(self.state)

    def test(self):
        """
        Prueba el LED.
        """
        for _ in range(5):
            self.on()
            utime.sleep(1)
            self.off()
            utime.sleep(1)


class Buzzer(Sensor):
    """
    Clase para representar un Buzzer.

    Attributes:
        pin: Pin del Buzzer
        state: Estado del Buzzer

    Methods:
        on:
            Enciende el Buzzer
        off:
            Apaga el Buzzer
        sound:
            Suena el Buzzer por x segundos
    """

    def __init__(self, name, pin):
        super().__init__(name, pin)
        self.state = False

    def on(self):
        """
        Enciende el Buzzer.
        """
        self.pin.on()
        self.state = True

    def off(self):
        """
        Apaga el Buzzer.
        """
        self.pin.off()
        self.state = False

    def sound(self, seconds=1):
        """
        Enciende el Buzzer.
        """
        self.pin.on()
        self.state = True
        sleep(seconds)
        self.pin.off()
        self.state = False

    def test(self):
        """
        Prueba el Buzzer.
        """
        self.sound()


class Servo(Sensor):
    """
    Clase para representar un Servo.

    Attributes:
        pin: Pin del Servo
        state: Estado del Servo

    Methods:
        on:
            Enciende el Servo
        off:
            Apaga el Servo
        sound:
            Suena el Servo por x segundos
    """

    def __init__(self, name, pin):
        super().__init__(name, pin)
        self.state = False
        self.pwm = PWM(self.pin)
        self.pwm.freq(50)

    def rotateTo(self, angle):
        """
        Rota el Servo a cierto ángulo.
        """
        self.pwm.duty_u16(angle)
        self.state = True

    def rotateCycle(self):
        """
        Rota el Servo un ciclo.
        """
        for angle in range(2000, 8000, 1000):
            self.rotateTo(angle)
            utime.sleep(1)

    def test(self):
        """
        Prueba el Servo.
        """
        for _ in range(5):
            self.rotateTo(8000)
            utime.sleep(0.5)
            self.rotateTo(2000)
            utime.sleep(2)


class BaseMQ(object):
    """
    Clase base para los sensores MQ.

    Args:
        pinData: Pin de datos del sensor MQ
        pinHeater: Pin de calentador del sensor MQ
        boardResistance: Resistencia de la placa del sensor
        baseVoltage: Voltaje del Microcontrolador
        measuringStrategy: Estrategia de medición

    Attributes:
        _heater: Estado del calentador
        _cooler: Estado del enfriador
        _ro: Valor de Ro (Resistencia en aire limpio)
        _useSeparateHeater: Bandera para indicar el uso de un calentador separado
        _baseVoltage: Voltaje del Microcontrolador
        _lastMesurement: Última medición del sensor
        _rsCache: Cache de la resistencia
        dataIsReliable: Bandera para indicar que los datos son confiables
        pinData: Pin de datos del sensor
        measuringStrategy: Estrategia de medición
        _boardResistance: Resistencia de la placa
        _pinHeater: Pin de calentador del sensor
        _stateCalibrate: Estado de calibración

    Methods:
        getRoInCleanAir:
            Devuelve el valor de Ro en aire limpio, funcion abstracta
        calibrate:
            Calibra el sensor
        heaterPwrHigh:
            Enciende el calentador
        heaterPwrLow:
            Baja la potencia del calentador
        heaterPwrOff:
            Apaga el calentador
        __calculateResistance__:
            Calcula la resistencia
        __readRs__:
            Lee la resistencia
        readScaled:
            Calculo matemático para escalar la lectura a un valor real
        readRatio:
            Calculo de la relación de la resistencia con Ro 
        heatingCompleted:
            Comprueba si el calentador se ha calentado
        coolanceCompleted:
            Comprueba si el enfriador se ha enfriado
        cycleHeat:
            Ciclo de calentamiento
        atHeatCycleEnd:
            Comprueba si el ciclo de calentamiento ha terminado
    """
    # Constantes de la clase
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
        self._stateCalibrate = False

        if pinHeater != -1:
            self.useSeparateHeater = True
            self.pinHeater = Pin(pinHeater, Pin.OUT)

    def getRoInCleanAir(self):
        """
        Devuelve el valor de Ro en aire limpio, funcion abstracta
        """

        raise NotImplementedError("Please Implement this method")

    def calibrate(self, ro=-1):
        """
        Calibra el sensor.

        Args:
            ro: Valor de Ro (Resistencia en aire limpio)
        """

        if ro == -1:
            ro = 0
            print("\tCalibrating Gas Sensor:")
            for i in range(0, self.MQ_SAMPLE_TIMES + 1):
                print("\t\tStep {0}".format(i))
                ro += self.__calculateResistance__(self.pinData.read_u16())
                utime.sleep_ms(self.MQ_SAMPLE_INTERVAL)
            ro = ro/(self.getRoInCleanAir() * self.MQ_SAMPLE_TIMES)
        self._ro = ro
        self._stateCalibrate = True

    def heaterPwrHigh(self):
        """
        Enciende el calentador.
        """

        # digitalWrite(_pinHeater, HIGH)
        # _pinHeater(1)
        if self._useSeparateHeater:
            self._pinHeater.on()
            pass
        self._heater = True
        self._prMillis = utime.ticks_ms()

    def heaterPwrLow(self):
        """
        Baja la potencia del calentador.
        """

        # analogWrite(_pinHeater, 75)
        self._heater = True
        self._cooler = True
        self._prMillis = utime.ticks_ms()

    def heaterPwrOff(self):
        """
        Apaga el calentador.
        """

        if self._useSeparateHeater:
            self._pinHeater.off()
            pass
        _pinHeater(0)
        self._heater = False

    def __calculateResistance__(self, rawAdc):
        """
        Calcula la resistencia.

        Args:
            rawAdc: Valor del ADC

        Returns:
            float: Resistencia calculada
        """

        vrl = rawAdc*(self._baseVoltage / 65535)
        rsAir: float = (self._baseVoltage - vrl)/vrl*self._boardResistance
        return rsAir

    def __readRs__(self):
        """
        Lee la resistencia por medio de promedio de muestras en intervalos de tiempos especificos.

        Returns:
            float: Promedio de los valores leidos.
        """

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
        """
        Calculo matemático para escalar la lectura a un valor real.

        Args:
            a: Valor de la constante especifica para cada tipo de medicion.
            b: Valor de la constante especifica para cada tipo de medicion.

        Returns:
            float: Valor escalado
        """

        return exp((log(self.readRatio())-b)/a)

    def readRatio(self):
        """
        Calculo de la relación de la resistencia con Ro.

        Returns:
            float: Valor de la relación
        """

        return self.__readRs__()/self._ro

    def heatingCompleted(self):
        """
        Comprueba si el calentador se ha calentado.

        Returns:
            bool: True si se ha calentado, False si no
        """

        if (self._heater) and (not self._cooler) and (utime.ticks_diff(utime.ticks_ms(), self._prMillis) > self.MQ_HEATING_PERIOD):
            return True
        return False

    def coolanceCompleted(self):
        """
        Comprueba si el enfriador se ha enfriado.

        Returns:
            bool: True si se ha enfriado, False si no
        """

        if (self._heater) and (self._cooler) and (utime.ticks_diff(utime.ticks_ms(), self._prMillis) > self.MQ_COOLING_PERIOD):
            return True
        return False

    def cycleHeat(self):
        """
        Ciclo de calentamiento.

        Returns:
            bool: True si se ha calentado, False si no
        """

        self._heater = False
        self._cooler = False
        self.heaterPwrHigh()
        print("Heated sensor")

    def atHeatCycleEnd(self):
        """
        Comprueba si el ciclo de calentamiento ha terminado.
        Se utiliza para cambiar el estado de calentamiento y enfriamiento.

        Returns:
            bool: True si se ha calentado, False si no
        """

        if self.heatingCompleted():
            self.heaterPwrLow()
            print("Cool sensor")
            return False
        if self.coolanceCompleted():
            self.heaterPwrOff()
            return True
        return False


class MQ2(BaseMQ):
    # Constantes de la clase
    MQ2_RO_BASE = float(9.83)

    """
    Clase para el sensor MQ2 (Sensor de gas).

    Args:
        pinData: Pin de datos del sensor MQ2
        pinHeater: Pin de calentador del sensor MQ2
        boardResistance: Resistencia de la placa del sensor
        baseVoltage: Voltaje del Microcontrolador
        measuringStrategy: Estrategia de medición

    Attributes:
        MQ2_RO_BASE: Valor de Ro (Resistencia en aire limpio)
    
    Methods:
        readLPG:
            Lee el valor de LPG
        readMethane:
            Lee el valor del Metano
        readSmoke:
            Lee el valor de la condensación de humo
        readHydrogen:
            Lee el valor del Hidrógeno
        getRoInCleanAir:
            Devuelve el valor de Ro en aire limpio
    """

    def __init__(self, pinData, pinHeater=-1, boardResistance=10, baseVoltage=3.3, measuringStrategy=BaseMQ.STRATEGY_ACCURATE):
        super().__init__(pinData, pinHeater, boardResistance, baseVoltage, measuringStrategy)

    def readLPG(self):
        """
        Lee el valor de LPG.

        Returns:
            float: Valor de LPG
        """
        return self.readScaled(-0.45, 2.95)

    def readMethane(self):
        """
        Lee el valor del Metano.

        Returns:
            float: Valor del Metano.
        """
        return self.readScaled(-0.38, 3.21)

    def readSmoke(self):
        """
        Lee el valor de la condensación de humo.

        Returns:
            float: Valor de la condensación de humo.
        """
        return self.readScaled(-0.42, 3.54)

    def readHydrogen(self):
        """
        Lee el valor del Hidrógeno.

        Returns:
            float: Valor del Hidrógeno.
        """
        return self.readScaled(-0.48, 3.32)

    def getRoInCleanAir(self):
        """
        Devuelve el valor de Ro en aire limpio.

        Returns:
            float: Valor de Ro en aire limpio.
        """
        return self.MQ2_RO_BASE


class MFRC522:
    """
    Clase para el sensor MFRC522 (Lector RFID).

    Args:
        sck: Pin de reloj
        mosi: Pin de datos de salida
        miso: Pin de datos de entrada
        rst: Pin de reset
        cs: Pin de selección
        baudrate: Velocidad de transmisión
        spi_id: ID del SPI

    Attributes:
        sck: Pin de reloj
        mosi: Pin de datos de salida
        miso: Pin de datos de entrada
        rst: Pin de reset
        cs: Pin de selección
        spi: Objeto SPI
        REQIDL: Constante de solicitud de identificación
        REQALL: Constante de solicitud de todos
        AUTHENT1A: Constante de autenticación 1A
        AUTHENT1B: Constante de autenticación 1B
        PICC_ANTICOLL1: Constante de anticollisión 1
        PICC_ANTICOLL2: Constante de anticollisión 2
        PICC_ANTICOLL3: Constante de anticollisión 3

    Methods:
        _wreg:
            Escribe un registro usando SPI.
        _rreg:
            Lee un registro usando SPI.
        _sflags:
            Establece banderas de un registro.
        _cflags:
            Limpia banderas de un registro.
        _tocard:
            Envia datos a la tarjeta y recibe datos de la tarjeta.
        _crc:
            Calcula el CRC (Verificación de Redundancia Cíclica).
        init:
            Inicializa el sensor prendiendo la antenna y reiniciando el sensor.
        reset:  
            Reinicia el sensor.
        antenna_on: 
            Enciende la antena.
        request:    
            Solicita la identificación de la tarjeta (UID - Unique Identifier).
        anticoll:
            Anticolisión con la información de la tarjeta.
        PcdSelect:
            Selecciona la tarjeta enviando su UID.
        SelectTag:
            Selecciona la etiqueta por su UID.
        tohexstring:
            Convierte un arreglo de bytes a una cadena de texto.
        SelectTagSN:
            Selecciona la etiqueta por su número de serie.
        auth:
            Autentica mandando la llave de la tarjeta.
        authKeys:
            Autentica usando compuertas lógicas a traves de la llave A o B.
        stop_crypto1:
            Detiene la autenticación
        read:
            Lee un bloque de la tarjeta.
        write:
            Escribe un bloque de la tarjeta.
        writeSectorBlock:
            Escribe un bloque de un sector en la tarjeta.
        readSectorBlock:
            Lee un bloque de un sector en la tarjeta.
        MFRC522_DumpClassic1K:
            Recopila los datos de una tarjeta Mifare Classic 1K.
    """
    #  Constantes de la clase
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
        if board == 'rp2':
            self.spi = SPI(spi_id, baudrate=baudrate,
                           sck=self.sck, mosi=self.mosi, miso=self.miso)
        else:
            raise RuntimeError("Unsupported platform")

        self.rst.value(1)

    def _wreg(self, reg, val):
        """
        Escribe un registro usando SPI.

        Args:
            reg: Registro
            val: Valor
        """
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.spi.write(b'%c' % int(0xff & val))
        self.cs.value(1)

    def _rreg(self, reg):
        """
        Lee un registro usando SPI.

        Args:
            reg: Registro

        Returns:
            int: Valor del registro
        """
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sflags(self, reg, mask):
        """
        Establece banderas de un registro.

        Args:
            reg: Registro
            mask: Máscara
        """
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        """
        Limpia banderas de un registro.

        Args:
            reg: Registro
            mask: Máscara
        """

        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):
        """
        Envia datos a la tarjeta y recibe datos de la tarjeta.

        Args:
            cmd: Comando
            send: Datos a enviar

        Returns:
            int: Estado
            list: Datos recibidos
            int: Bits
        """
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
        """	
        Calcula el CRC (Verificación de Redundancia Cíclica).

        Args:
            data: Datos

        Returns:
            list: Datos con el CRC
        """

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
        """
        Inicializa el sensor prendiendo la antenna y reiniciando el sensor.
        """

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
        """
        Reinicia el sensor.
        """

        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):
        """
        Enciende la antena.

        Args:
            on: Estado de la antena
        """

        print("Antena ON...")
        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def request(self, mode):
        """
        Solicita la identificación de la tarjeta (UID - Unique Identifier).

        Args:
            mode: Modo de solicitud

        Returns:
            int: Estado
            int: Bits
        """
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])

        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR
        return stat, bits

    def anticoll(self, anticolN):
        """
        Anticolisión con la información de la tarjeta.

        Args:
            anticolN: Anticolisión

        Returns:
            int: Estado
            list: Datos recibidos
        """

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
        """
        Selecciona la tarjeta enviando su UID.

        Args:
            serNum: Número de serie
            anticolN: Anticolisión

        Returns:
            int: Estado
        """

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
        """
        Selecciona la etiqueta por su UID.

        Args:
            uid: UID

        Returns:
            int: Estado
            list: UID
        """

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
        """
        Convierte un arreglo de bytes a una cadena de texto.

        Args:
            v: Arreglo de bytes

        Returns:
            str: Cadena de texto
        """

        s = "["
        for i in v:
            if i != v[0]:
                s = s + ", "
            s = s + "0x{:02X}".format(i)
        s = s + "]"
        return s

    def SelectTagSN(self):
        """
        Selecciona la etiqueta por su número de serie.

        Returns:
            tuple[Literal, list]: Estado, UID
        """

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
        """
        Autentica mandando la llave de la tarjeta.

        Args:
            mode: Modo de autenticación
            addr: Dirección
            sect: Sector
            ser: Serie

        Returns:
            tuple[Literal, list, int]: Estado, Datos recibidos, Bits
        """
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def authKeys(self, uid, addr, keyA=None, keyB=None):
        """
        Autentica usando compuertas lógicas a traves de la llave A o B.

        Args:
            uid: UID
            addr: Dirección de memoria
            keyA: Llave A
            keyB: Llave B

        Returns:
            int: Estado
        """

        status = self.ERR
        if keyA is not None:
            status = self.auth(self.AUTHENT1A, addr, keyA, uid)
        elif keyB is not None:
            status = self.auth(self.AUTHENT1B, addr, keyB, uid)
        return status

    def stop_crypto1(self):
        """
        Detiene la autenticación.
        """

        self._cflags(0x08, 0x08)

    def read(self, addr):
        """
        Lee un bloque de la tarjeta.

        Args:
            addr: Dirección de memoria

        Returns:
            tuple[Literal, list]: Estado, Datos recibidos
        """

        data = [0x30, addr]
        data += self._crc(data)
        (stat, recv, _) = self._tocard(0x0C, data)
        return stat, recv

    def write(self, addr, data):
        """
        Escribe un bloque de la tarjeta.

        Args:
            addr: Dirección de memoria
            data: Datos

        Returns:
            int: Estado
        """

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
        """
        Escribe un bloque de un sector en la tarjeta.

        Args:
            uid: UID
            sector: Sector del bloque
            block: Bloque de memoria
            data: Datos
            keyA: Llave A
            keyB: Llave B

        Returns:
            int: Estado
        """

        absoluteBlock = sector * 4 + (block % 4)
        if absoluteBlock > 63:
            return self.ERR
        if len(data) != 16:
            return self.ERR
        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR:
            return self.write(absoluteBlock, data)
        return self.ERR

    def readSectorBlock(self, uid, sector, block, keyA=None, keyB=None):
        """
        Lee un bloque de un sector en la tarjeta.

        Args:
            uid: UID
            sector: Sector del bloque
            block: Bloque de memoria
            keyA: Llave A
            keyB: Llave B

        Returns:
            tuple[Literal, list]: Estado, Datos recibidos
        """
        absoluteBlock = sector * 4 + (block % 4)
        if absoluteBlock > 63:
            return self.ERR, None
        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR:
            return self.read(absoluteBlock)
        return self.ERR, None

    def MFRC522_DumpClassic1K(self, uid, Start=0, End=64, keyA=None, keyB=None):
        """
        Recopila los datos de una tarjeta Mifare Classic 1K.

        Args:
            uid: UID
            Start: Bloque inicial
            End: Bloque final
            keyA: Llave A
            keyB: Llave B

        Returns:
            int: Estado
        """
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
# Inicializacion de sensores
# ----------------------------------
def initSensors():
    cList["Foco1_Jardin"] = Led("Foco1_Jardin", getattr(config, "PIN_JC_LED"))
    cList["Foco2_Jardin"] = Led("Foco2_Jardin", getattr(config, "PIN_JT_LED"))
    sList["Luz_Jardin"] = Sensor("Luz_Jardin", getattr(config, "PIN_JSL"))
    sList["Humedad_Jardin"] = Sensor(
        "Humedad_Jardin", getattr(config, "PIN_JH"))

    cList["Foco_Cocina"] = Led("Foco_Cocina", getattr(config, "PIN_C_LED"))
    cList["Alarma_Cocina"] = Buzzer(
        "Alarma_Cocina", getattr(config, "PIN_C_BUZZER"))
    sList["Gas_Cocina"] = Sensor("Gas_Cocina", getattr(config, "PIN_CG"))

    cList["Foco_Habitacion"] = Led(
        "Foco_Habitacion", getattr(config, "PIN_H_LED"))
    cList["Servomotor_Habitacion"] = Servo("Servomotor_Habitacion",
                                           getattr(config, "PIN_H_SERVO"))
    sList["Temperatura_Habitacion"] = Sensor(
        "Temperatura_Habitacion", getattr(config, "PIN_HT"))

    cList["Foco_Garage"] = Led("Foco_Garage", getattr(config, "PIN_G_LED"))
    cList["Servomotor_Garage"] = Servo(
        "Servomotor_Garage", getattr(config, "PIN_G_SERVO"))
    cList["Alarma_Garage"] = Buzzer(
        "Alarma_Garage", getattr(config, "PIN_G_BUZZER"))

    cList["Foco_Entrada"] = Led("Foco_Entrada", getattr(config, "PIN_E_LED"))
    cList["Alarma_Entrada"] = Buzzer(
        "Alarma_Entrada", getattr(config, "PIN_E_BUZZER"))
    sList["Proximidad_Entrada"] = Sensor(
        "Proximidad_Entrada", getattr(config, "PIN_EIR"))
    sList["Tarjeta_Entrada"] = Sensor(
        "Tarjeta_Entrada", getattr(config, "PIN_ERFID"))

    # Test components
    for component in cList.values():
        print(f"Testing component: {component.name}")
        component.test()
        userInput = input("Is working? Y/n:")
        if userInput == "n":
            print("Exiting...")
            return False

    # Calibrate sensors
    for sensor in sList.values():
        print(f"Calibrating sensor: {sensor.name}")
        sensor.calibrate()


def readDataSensors():
    data = {}
    for sensor in sList.values():
        data[sensor.name] = sensor.read()
    return data


def doActionComponent(name, action):
    if name in cList:
        component = cList[name]
        if action == "on":
            component.on()
        elif action == "off":
            component.off()
        elif action == "toggle":
            component.toggle()
        else:
            print(f"Action {action} not found")
    else:
        print(f"Component {name} not found")
