import threading
import httplib
import time

SHUTDOWN_SIGNAL = False
THREAD_STARTED = False


def start_poll():
    global THREAD_STARTED

    if not THREAD_STARTED:
        threading.Thread(target=shutdown_signal_poll).start()
        THREAD_STARTED = True


def shutdown():
    return SHUTDOWN_SIGNAL


def is_valid_time(dtime):
    try:
        time.strptime(dtime, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def shutdown_signal_poll():
    conn = httplib.HTTPConnection("169.254.169.254")

    global SHUTDOWN_SIGNAL

    while True:
        conn.request("GET", "/latest/meta-data/spot/termination-time")

        response = conn.getresponse()

        msg = response.read()

        if response.status == 200:
            if is_valid_time(msg):
                SHUTDOWN_SIGNAL = True
                break

        time.sleep(5)

    conn.close()

    return


