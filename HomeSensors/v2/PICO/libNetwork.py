from time import sleep
import json
import urequests
import network


class handlerAPI:
    def __init__(self):
        self.url = None
        self.body = None
        self.response = None

    def setURL(self, url):
        self.url = url

    def checkAPI(self):
        print("Checking API...")
        # Parpadea LED rojo
        try:
            r = urequests.request("GET", self.url)
            if r.status_code == 200:
                return True
            return False
        except Exception as e:
            print("Error: ", e)
            return False

    def sendAPI(self, dataOut):
        print("Sending data...")
        # Parpadea LED verde
        try:
            jsonData = json.dumps(dataOut)
            r = urequests.request("POST", self.url, json=jsonData)
            self.response = r.json()
            r.close()
            return True
        except Exception as e:
            print("Error: ", e)
            return False

    def receiveAPI(self):
        print("Receiving data...")
        # Parpader LED azul
        r = urequests.request("GET", self.url)
        self.response = r.json()
        r.close()
        return self.response


def connectNet(ssid, pwd):
    print('Connecting to network...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, pwd)

    while not wlan.isconnected():
        print('Waiting for network...')
        # Mantener LED rojo, usa los parametros que tienes en el archivo de configuracion
        sleep(1)

    print('Network connected')
    print('Network config:', wlan.ifconfig())
    sleep(1)
    # Cambiar LED a verde
