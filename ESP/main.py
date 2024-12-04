import gc
import _thread
from time import sleep
from lib import libFirebase, libNetwork, libDevices


def t_readFirebase(firebase: libFirebase.FirebaseRealtime):
    while True:
        try:
            firebase.receiveDataDevices()
            gc.collect()
            sleep(0.5)
        except OSError:
            print("! Error: Connection lost!")


def main():
    print("! Sweep")
    libDevices.wipeAll()
    

    print("> Starting main...")
    gc.collect()
    libNetwork.connectWifi()

    roomsCatalog = libDevices.Rooms()
    firebase = libFirebase.FirebaseRealtime(roomsCatalog)

    _thread.start_new_thread(t_readFirebase, (firebase,))

    try:
        while True:
            dataSensors = roomsCatalog.readSensors()
            firebase.sendData(dataSensors)
            gc.collect()
            sleep(10)
    except Exception as e:
        print("<< Error: ", e)
    finally:
        _thread.exit()
        gc.collect()
    print("< Main finished!")
    return


if __name__ == "__main__":
    main()
