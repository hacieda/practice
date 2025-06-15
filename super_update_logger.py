# task 5

import sys
from datetime import datetime


class Formatter:
    def __init__(self, fmt: str = "%Y-%m-%d %H:%M:%S") -> None:
        self.fmt = fmt

    def format(self, message: str) -> str:
        timestamp: str = datetime.now().strftime(self.fmt)
      
        return f"[{timestamp}] {message}"


class Handler:
    def __init__(self, destination) -> None:
        self.destination = destination

    def emit(self, message: str) -> None:
        if self.destination in (sys.stdout, sys.stderr):
            self.destination.write(message + "\n")
          
        else:
            with open(self.destination, "a", encoding="utf-8") as file:
                file.write(message + "\n")


class Logger:
    def __init__(self, formatter: Formatter) -> None:
        self.formatter = formatter
        self.handlers = []

    def add_handler(self, handler: Handler) -> None:
        self.handlers.append(handler)

    def log(self, message: str) -> None:
        formatted: str = self.formatter.format(message)
      
        for handler in self.handlers:
            handler.emit(formatted)


if __name__ == "__main__":
    formatter = Formatter()
    logger = Logger(formatter)

    logger.add_handler(Handler(sys.stdout))
    logger.add_handler(Handler(sys.stderr))
    logger.add_handler(Handler("logfile.txt"))

    logger.log("Hello! This is a test log message.")
    logger.log("Another entry recorded in the log.")
