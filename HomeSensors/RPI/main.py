import queue
import sys
import threading
import traceback
import libConnect as libRPI

# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    qAPISend = queue.Queue()
    qAPIRecv = queue.Queue()
    stop = threading.Event()

    print("Init program...")

    # *Conexion con RPI
    brRPI = libRPI.API(qAPISend, qAPIRecv)

    apiSender = threading.Thread(
        target=brRPI.senderWorker, args=[stop], daemon=True)
    apiListener = threading.Thread(
        target=brRPI.listenerWorker, args=[stop], daemon=True)

    # *Conexion con la PICO
    connPICO: libRPI.Connection = libRPI.initConnectPico()
    apiSender.start()
    apiListener.start()
    brPICO = libRPI.senderListener(connPICO, qAPISend, qAPIRecv)
    sel = connPICO.selector
    try:
        while not stop.is_set():
            events = sel.select(timeout=None)
            for key, mask in events:
                try:
                    recollect = brPICO.processEvents(mask)
                except Exception:
                    print(
                        f"Main: Error: Exception for {connPICO.addr}:\n"
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
