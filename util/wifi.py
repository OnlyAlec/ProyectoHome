import socket
import network
import utime

# Configuración de la conexión WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('INFINITUM1B29_2.4', '3vq4v7vPsV')

while not wlan.isconnected():
    pass
print('Conexión WiFi establecida, IP:', wlan.ifconfig()[0])

# Creación del socket
s = socket.socket()
host = '192.168.1.204'
port = 45871
s.connect((host, port))

contador = 0

while True:
    contador += 1
    mensaje = f'Valor del contador: {contador}\n'
    s.send(mensaje.decode('utf-8'))  # Convierte el mensaje a bytes y lo envía
    utime.sleep(1)  # Espera 1 segundo antes de enviar el siguiente valor

s.close()
