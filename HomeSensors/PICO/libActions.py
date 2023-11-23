"""Librerias."""
from machine import PWM
import config


def ledChange(**kwargs) -> bool:
    """
    Funcion para cambiar el estado de un led.

    Args:
        `**kwargs`: Diccionario con los parametros del led.

    Returns:
        bool: True si se cambio el estado, False en caso contrario.

    Raises:
        Exception: Error al cambiar el estado del led.
    """

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
    """
    Funcion para cambiar el estado de un servo.

    Args:
        `**kwargs`: Diccionario con los parametros del servo.

    Returns:
        bool: True si se cambio el estado, False en caso contrario.

    Raises:
        Exception: Error al cambiar el estado del servo.
    """

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
    """
    Funcion para cambiar el estado de un buzzer.

    Args:
        `**kwargs`: Diccionario con los parametros del buzzer.

    Returns:
        bool: True si se cambio el estado, False en caso contrario.

    Raises:
        Exception: Error al cambiar el estado del buzzer.
    """

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
