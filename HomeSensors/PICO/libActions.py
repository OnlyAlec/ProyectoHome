import utime
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
    servo.freq(50)

    if state == "ON":
        servo.duty_u16(8000)
    else:
        servo.duty_u16(2000)
    return True


def buzzerAction(**kwargs):
    buzzer = globals()[kwargs["servo"]]
    state = getattr(config, kwargs["state"])
    time = kwargs.get("time")

    if state == "ON":
        buzzer.on()
        utime.sleep(time)
        buzzer.off()
    else:
        buzzer.off()
