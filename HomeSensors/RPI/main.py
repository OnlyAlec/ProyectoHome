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
    # stop_event = threading.Event()

    print("Init program...")
    connRPI: libRPI.Connection = libRPI.initConnectRPI(
        host="200.10.0.1", port=2050)
    connPICO: libRPI.Connection = libRPI.initConnectPico()

    # *Conexion con RPI
    brRPI = libRPI.API(connRPI, qAPIRecv, qAPISend)
    apiSender = threading.Thread(
        target=brRPI.senderWoker, args=[], daemon=True)
    apiListener = threading.Thread(
        target=brRPI.listenerWorker, args=[], daemon=True)

    apiSender.start()
    apiListener.start()

    # *Conexion con la PICO
    brPICO = libRPI.senderListener(connPICO, qAPISend)
    sel = connPICO.selector
    try:
        while True:
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
                    break
    finally:
        print("Waiting Threads...")
        apiSender.join()
        apiListener.join()

        print("Ending...")
        sel.close()
        sys.exit()
