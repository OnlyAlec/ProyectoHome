from machine import PWM
import config


def ledChange(**kwargs):
    try:
        state = kwargs["state"]
        led = getattr(config, kwargs["led"])
        print(f"\t # LED: {kwargs["led"]} -> {state}")

        if state == "ON":
            led.on()
        else:
            led.off()
    except Exception as e:
        print(f"\t\t !# Error: {e}")
        return False
    return True


def servoAction(**kwargs):
    try:
        state = kwargs["state"]
        servo = getattr(config, kwargs["servo"])
        print(f"\t # Servo: {kwargs["servo"]} -> {state}")
        pwmServo = PWM(servo)
        pwmServo.freq(50)

        if state == "ON":
            pwmServo.duty_u16(8000)
        else:
            pwmServo.duty_u16(2000)
    except Exception as e:
        print(f"\t\t !# Error: {e}")
        return False
    return True


def buzzerAction(**kwargs):
    try:
        buzzer = getattr(config, kwargs["buzzer"])
        state = kwargs["state"]
        print(f"\t # Buzzer: {kwargs["buzzer"]} -> {state}")

        if state == "ON":
            buzzer.on()
        else:
            buzzer.off()
    except Exception as e:
        print(f"\t\t !# Error: {e}")
        return False
    return True
