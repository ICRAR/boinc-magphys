__author__ = 'ict310'

from utils.shutdown_detection import start_poll, shutdown
import time

def main():
    i = 0

    try:
        while True:
            print "I am doing things! {0}".format(i)
            i += 1
            time.sleep(1)

            if shutdown() is True:
                raise SystemExit

    except SystemExit:
        print 'Exiting...'


if __name__ == "__main__":
    start_poll()
    main()