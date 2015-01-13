import threading
import httplib
import time

SHUTDOWN_SIGNAL = False
poll_thread = None


def start_poll():
    threading.Thread(target=shutdown_signal_poll).start()


def shutdown():
    return SHUTDOWN_SIGNAL


def is_valid_time(dtime):
    try:
        time.strptime(dtime, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def shutdown_signal_poll():
    # conn = httplib.HTTPConnection("169.254.169.254")
    conn = httplib.HTTPSConnection("dl.dropboxusercontent.com")

    global SHUTDOWN_SIGNAL

    while True:
        # conn.request("GET", "/latest/meta-data/spot/termination-time")
        conn.request("GET", "/u/20459810/Testing/teststatus.html")

        response = conn.getresponse()
        # print "status:{0}".format(response.status)

        msg = response.read()
        # print "response:{0}".format(msg)

        if response.status == 200:
            if is_valid_time(msg):
                SHUTDOWN_SIGNAL = True
                break

        time.sleep(5)

    conn.close()

    return


