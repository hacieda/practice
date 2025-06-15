from abc import ABC, abstractmethod
import math


class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        ...


class Rectangle(Shape):
    def __init__(self, length: float, width: float) -> None:
        self._length = length
        self._width = width

    def get_length(self) -> float:
        return self._length

    def get_width(self) -> float:
        return self._width

    def area(self) -> float:
        return self._length * self._width


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self._radius = radius

    def get_radius(self) -> float:
        return self._radius

    def area(self) -> float:
        return math.pi * (self._radius ** 2)


if __name__ == "__main__":
    figures: list[Shape] = [
        Rectangle(length=4, width=5),
        Circle(radius=3),
        Rectangle(length=2, width=7),
        Circle(radius=1)
    ]

    for fig in figures:
        print(f"{type(fig).__name__} area: {fig.area():.2f}")
