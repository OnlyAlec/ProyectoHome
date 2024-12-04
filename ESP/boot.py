# boot.py -- run on boot-up
from machine import Pin
from time import sleep
from neopixel import NeoPixel

# Configuración del pin y NeoPixel
pin = Pin(48, Pin.OUT)
np = NeoPixel(pin, 1)

# Factor de luminosidad (0.0 a 1.0)
brightness = 0.2  # Ajusta el brillo aquí (20% de luminosidad)


def wheel(pos, brightness=1.0):
    # Devuelve un color RGB basado en la posición (0-255)
    if pos < 85:
        return (
            int((255 - pos * 3) * brightness),
            int((pos * 3) * brightness),
            0,
        )
    elif pos < 170:
        pos -= 85
        return (
            0,
            int((255 - pos * 3) * brightness),
            int((pos * 3) * brightness),
        )
    else:
        pos -= 170
        return (
            int((pos * 3) * brightness),
            0,
            int((255 - pos * 3) * brightness),
        )


def rainbow_cycle_once(np, brightness=1.0, wait=0.05):
    for j in range(256):  # Ciclo a través de 256 colores
        for i in range(1):  # En este caso, un solo LED
            rc_index = (i * 256 // 1 + j) & 255
            np[i] = wheel(rc_index, brightness)
        np.write()
        sleep(wait)
    # Al final del ciclo, establece el color en verde
    np[0] = (0, int(255 * brightness), 0)
    np.write()


# Ejecutar el efecto arcoíris una vez
rainbow_cycle_once(np, brightness=brightness)
