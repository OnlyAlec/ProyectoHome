"""Librerias."""
import queue
import sys
import threading
import traceback
import libConnect as libRPI

if __name__ == '__main__':
    # *Variables
    print("Init program...")
    qAPISend = queue.Queue()
    qAPIRecv = queue.Queue()
    stop = threading.Event()

    # *Conexion con RPI por API
    brRPI = libRPI.API(qAPISend, qAPIRecv)
    apiSender = threading.Thread(
        target=brRPI.senderWorker, args=[stop], daemon=True)
    apiListener = threading.Thread(
        target=brRPI.listenerWorker, args=[stop], daemon=True)

    # *Conexion con la PICO por socket
    connPICO: libRPI.Connection = libRPI.initConnectPico()
    brPICO = libRPI.senderListener(connPICO, qAPISend, qAPIRecv)
    sel = connPICO.selector

    # *Inicio de workers
    brRPI.getStateSensor()
    apiSender.start()
    apiListener.start()

    # !Main Loop
    try:
        while not stop.is_set():
            print("Main: Waiting Events...")
            events = sel.select(timeout=None)
            for key, mask in events:
                try:
                    recollect = brPICO.processEvents(mask)
                    if not recollect:
                        print("Main: Unknown Error...")
                        stop.set()
                except Exception:
                    print(
                        f"Main: Error: {connPICO.addr}:\n"
                        f"{traceback.format_exc()}"
                    )
                    connPICO.close()
                    stop.set()
    finally:
        print("Waiting Threads...")
        apiSender.join()
        apiListener.join()

        print("Ending...")
        sel.close()
        connPICO.close()
        sys.exit()
