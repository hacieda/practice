# task 3

import sys
from datetime import datetime


class Logger:
    def __init__(self, out_stream, time_formatter: str):
        self.out_stream = out_stream
        self.time_formatter: str = time_formatter

    def log(self, message: str):
        timestamp: str = datetime.datetime.now().strftime(self.time_formatter)
        print(f"{timestamp} {message}", file=self.out_stream)


if __name__ == "__main__":
    out_stream = sys.stderr
    time_formatter: str = "%Y-%m-%d %H:%M:%S"
    logger = Logger(out_stream, time_formatter)

    logger.log("Logging message")
