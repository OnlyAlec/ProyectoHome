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

    print("Init program...")

    # *Conexion con RPI
    brRPI = libRPI.API(qAPISend, qAPIRecv)

    apiSender = threading.Thread(
        target=brRPI.senderWorker, args=[], daemon=True)
    apiListener = threading.Thread(
        target=brRPI.listenerWorker, args=[], daemon=True)

    apiSender.start()
    apiListener.start()

    # *Conexion con la PICO
    connPICO: libRPI.Connection = libRPI.initConnectPico()
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
