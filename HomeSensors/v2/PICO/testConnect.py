import socket
import network
import machine

ledPin = machine.Pin("LED", machine.Pin.OUT)


def apMode(ssid, password):
    """
        Description: This is a function to activate AP mode

        Parameters:

        ssid[str]: The name of your internet connection
        password[str]: Password for your internet connection

        Returns: Nada
    """
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)

    while ap.active() is False:
        pass

    print('AP Mode Activated --> SSID: ' + ssid)
    print('IP Address To Connect : ' + ap.ifconfig()[0])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        ledPin.on()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        print('Content = %s' % str(request))
        response = "Hello World!"
        conn.send(response)
        print('Connection closed')
        conn.close()
        ledPin.off()


apMode("HomeIotPico", "HomeIoT@Alec")
