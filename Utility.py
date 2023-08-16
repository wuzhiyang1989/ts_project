import datetime
from threading import Lock

print_lock = Lock()

def formatPrinting(buffer):
    print_lock.acquire()
    dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    print("[INFO] %s   [INF0] %s " % (dt_ms, buffer))
    print_lock.release()
