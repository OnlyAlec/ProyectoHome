from machine import PWM
import config


def ledChange(**kwargs):
    state = kwargs["state"]
    led = getattr(config, kwargs["led"])
    print(f"\t\t # LED: {led} -> {state}")

    if state == "ON" and led.value() == 0:
        led.on()
        return True
    if state == "OFF" and led.value() == 1:
        led.off()
        return True
    return False


def servoAction(**kwargs):
    state = kwargs["state"]
    servo = getattr(config, kwargs["servo"])
    pwmServo = PWM(servo)
    pwmServo.freq(50)

    if state == "ON":
        pwmServo.duty_u16(8000)
    else:
        pwmServo.duty_u16(2000)
    return True


def buzzerAction(**kwargs):
    buzzer = getattr(config, kwargs["buzzer"])
    state = kwargs["state"]

    if state == "ON":
        buzzer.on()
    else:
        buzzer.off()
