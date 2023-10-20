from machine import Pin, PWM
import utime

servo = Pin(17, Pin.OUT)
pwmServo = PWM(servo)
pwmServo.freq(50)


if __name__ == '__main__':

    while True:
        pwmServo.duty_u16(8000)
        utime.sleep(2)
        pwmServo.duty_u16(2000)
        utime.sleep(2)
