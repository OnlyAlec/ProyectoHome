import network


def connectWifi():
    print("> Starting Wifi...")
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        wlan.connect("LaSalleWifi", "")
        while not wlan.isconnected():
            pass
        print(">> Connected to WiFi!")
        print("< IP Address:", wlan.ifconfig()[0])
        return
    print("< Wifi already connected!")
    return
