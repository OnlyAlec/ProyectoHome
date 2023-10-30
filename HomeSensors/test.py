# import socket
# import selectors
# import json
# import sys
# import struct
# import io
# import traceback
# from main_pico import actions
import network

if __name__ == '__main__':
    print("Starting server...")
    print("Connecting...", end=" ")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Macuco', "DOMINGO.2022")
