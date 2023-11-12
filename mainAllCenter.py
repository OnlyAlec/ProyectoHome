import threading
import queue
from dotenv import load_dotenv
from libConnectRPI import initConnectRPI, listenRPIWorker
from libConnectAPI import listenAPIWorker, senderAPIWorker

load_dotenv()
qRPI = queue.Queue()
qAPI = queue.Queue()
conn = None


if __name__ == '__main__':
    print("Init Center RPI..")
    conn = initConnectRPI()

    listenRPI = threading.Thread(target=listenRPIWorker,
                                 args=(conn, qRPI), daemon=True)
    listenAPI = threading.Thread(target=listenAPIWorker,
                                 args=(qAPI), daemon=True)
    senderAPI = threading.Thread(target=senderAPIWorker,
                                 args=(qAPI), daemon=True)

    listenRPI.start()
    listenRPI.start()
    senderAPI.start()
