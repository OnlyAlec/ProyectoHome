from machine import Pin, PWM, ADC
from libSensors import MQ2, MFRC522
import utime

# JARDIN ---------------------------
LED_JARDIN = Pin(2, Pin.OUT)
LED_JARDIN_LUZ = Pin(4, Pin.OUT)
LUZ = ADC(26)
HUMEDAD = ADC(28)

# COCINA ---------------------------
BUZZER_COCINA = Pin(6, Pin.OUT)
LED_COCINA = Pin(7, Pin.OUT)
GAS = MQ2(pinData=27, baseVoltage=3.3)

# HABITACION ---------------------------
SERVO_HABITACION = PWM(Pin(8, Pin.OUT))
SERVO_HABITACION.freq(50)
LED_HABITACION = Pin(9, Pin.OUT)
TEMP = ADC(4)

# GARAGE ---------------------------
LED_GARAGE = Pin(10, Pin.OUT)
SERVO_GARAGE = PWM(Pin(11, Pin.OUT))
SERVO_GARAGE.freq(50)
BUZZER_GARAGE = Pin(12, Pin.OUT)

# ENTRADA ---------------------------
IR = Pin(13, Pin.IN)
BUZZER_ENTRADA = Pin(14, Pin.OUT)
LED_ENTRADA = Pin(15, Pin.OUT)
RFID = MFRC522(spi_id=0, sck=18, cs=17, mosi=19, miso=16, rst=20)


def blinkLed(led, times=1, delay=0.5):
    for i in range(times):
        led.value(1)
        utime.sleep(delay)
        led.value(0)
        utime.sleep(delay)


def moveServo(servo, times=1, delay=0.5):
    for i in range(times):
        servo.duty_u16(8000)
        utime.sleep(delay)
        servo.duty_u16(1500)
        utime.sleep(delay)


def blinkBuzzer(buzzer, times=1, delay=1.5):
    for i in range(times):
        buzzer.value(1)
        utime.sleep(delay)
        buzzer.value(0)
        utime.sleep(delay)


def jardin():
    print("Jardin ---------------------------------")
    print("Luz: ", LUZ.read_u16())
    print("Humedad: ", HUMEDAD.read_u16())

    print("LED -> LED_JARDIN")
    blinkLed(LED_JARDIN, 5)
    print("LED -> LED_JARDIN_LUZ")
    blinkLed(LED_JARDIN_LUZ, 5)

    print("")


def cocina():
    print("Cocina ---------------------------------")
    GAS.calibrate()
    print("Gas: ", GAS.readMethane())

    print("BUZZER -> BUZZER_COCINA")
    blinkBuzzer(BUZZER_COCINA, 5)
    print("LED -> LED_COCINA")
    blinkLed(LED_COCINA, 5)

    print("")


def habitacion():
    print("Habitacion ---------------------------------")
    print("Temp: ", TEMP.read_u16())

    print("SERVO -> SERVO_HABITACION")
    moveServo(SERVO_HABITACION, 5)
    print("LED -> LED_HABITACION")
    blinkLed(LED_HABITACION, 5)

    print("")


def garage():
    print("Garage ---------------------------------")

    print("SERVO -> SERVO_GARAGE")
    moveServo(SERVO_GARAGE, 5)
    print("LED -> LED_GARAGE")
    blinkLed(LED_GARAGE, 5)
    print("BUZZER -> BUZZER_GARAGE")
    blinkBuzzer(BUZZER_GARAGE, 5)

    print("")


def entrada():
    print("Entrada ---------------------------------")
    print("IR: ", IR.value())
    print("RFID: ", RFID.request(RFID.REQIDL))

    print("BUZZER -> BUZZER_ENTRADA")
    blinkBuzzer(BUZZER_ENTRADA, 5)
    print("LED -> LED_ENTRADA")
    blinkLed(LED_ENTRADA, 5)

    print("")


if __name__ == '__main__':
    print("Init program...")
    LED_JARDIN.value(0)
    LED_COCINA.value(0)
    LED_HABITACION.value(0)
    LED_GARAGE.value(0)
    LED_ENTRADA.value(0)
    BUZZER_COCINA.value(0)
    BUZZER_GARAGE.value(0)
    BUZZER_ENTRADA.value(0)
    LED_JARDIN_LUZ.value(0)

    while True:
        print("Selecciona un espacio a revisar:")
        print("1. Jardin")
        print("2. Cocina")
        print("3. Habitacion")
        print("4. Garage")
        print("5. Entrada")
        print("6. Todos")

        option = input("Opcion: ")

        if option == "1":
            jardin()
        elif option == "2":
            cocina()
        elif option == "3":
            habitacion()
        elif option == "4":
            garage()
        elif option == "5":
            entrada()
        elif option == "6":
            jardin()
            cocina()
            habitacion()
            garage()
            entrada()
        else:
            print("Opcion invalida")
