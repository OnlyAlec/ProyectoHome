import network
import utime


def connectServer():
    print("Connecting...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Alec Honor', "DarklinkA")

    while not wlan.isconnected():
        pass

    print('Connect!, IP:', wlan.ifconfig()[0])
    return wlan


if __name__ == '__main__':
    wlanServer = connectServer()
    while True:
        print(wlanServer.status())
        utime.sleep(5)
