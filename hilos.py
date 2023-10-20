import time
import _thread
from machine import Pin, PWM


def task(idTask):
    print('Iniciando LED - ID: ', idTask)
    while True:
        led = Pin("LED", Pin.OUT)
        led.high()
        time.sleep(1)
        led.low()
        time.sleep(2)
        print('done')


def servoFn(idTask):
    print('Iniciando servo - ID: ', idTask)
    servo = Pin(17, Pin.OUT)
    pwmServo = PWM(servo)
    pwmServo.freq(50)
    while True:
        pwmServo.duty_u16(8000)
        time.sleep(0.5)
        pwmServo.duty_u16(2000)
        time.sleep(0.5)


_thread.start_new_thread(task, (1,))
servoFn(2)
