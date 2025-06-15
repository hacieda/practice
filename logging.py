import datetime
import sys


def log(message):
    t = datetime.datetime.now()
    time_str = t.strftime("[%Y-%m-%d %H-%M-%S]")
    print(time_str + " " + message, file=sys.stderr)

log("Test message")
