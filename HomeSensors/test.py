import socket
# import selectors
# import json
import sys
# import struct
# import io
# import traceback
# from main_pico import actions
import network
import utime

if __name__ == '__main__':
    print("Starting server...")
    print("Connecting...", end=" ")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    utime.sleep(1)
    wlan.active(True)
    # wlan.connect("Alec Honor", "DarklinkA")
    wlan.connect('RPI_Home', "Home@IoT")
    while not wlan.isconnected():
        print("Not connected!")
    addr = ("200.10.0.6", 8080)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(addr)
        print(f'\tOK!:  {addr}')
    except OSError as e:
        print(f'\n\tFailed!: {e}')
        sys.exit()
