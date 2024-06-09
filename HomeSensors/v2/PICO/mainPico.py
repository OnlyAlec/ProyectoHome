import _thread
from libSensors import initSensors, readDataSensors, doActionComponent
from libNetwork import connectNet, handlerAPI
import machine


def networkWorker(apiConnect):
    # *Hilo 1: Todo relacionado con recepcion de datos y actuadores
    apiConnect.setURL("https://api.homeiot.online/v.2/getStates")
    while True:
        print("W1: Receiving data...")
        # *Recibo datos
        dataRes = apiConnect.receiveAPI()
        # *Proceso datos
        if dataRes:
            for sensor, action in dataRes.items():
                doActionComponent(sensor, action)


if __name__ == '__main__':
    print("Init program...")
    api = handlerAPI()
    if not initSensors():
        print("Error initializing sensors!")
        machine.reset()

    # *Conectar a la red y comprobar internet
    connectNet("SSID", "PWD")
    api.setURL("https://api.homeiot.online/v.2/checkConnection")
    if not api.checkAPI():
        print("No Internet Available!")
        machine.reset()

    # *Iniciar hilos
    _thread.start_new_thread(networkWorker, (api,))

    # *Hilo 0: Todo relacionado con sensores y envio de datos
    cycleLectures = 0
    # *Calibro los sensores
    # *Lee datos
    while True:
        print("W0: Reading sensors data...")
        cycleLectures += 1
        data = readDataSensors()
        # *Envio datos
        api.sendAPI(data)
