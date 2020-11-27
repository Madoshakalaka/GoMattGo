from enum import Enum, auto


class Color(Enum):
    WHITE = 0
    BLACK = 1


class Piece:
    def __init__(self, row: int, col: int, color: Color):
        self._row = row
        self._col = col
        self._color = color

    def __repr__(self):
        return f"Piece<{self.row} {self.col}>"

    def __hash__(self):
        return hash((self.row, self.col, self.color))

    @property
    def adjacent_coordinates(self):
        coords = []
        if self.row >= 1:
            coords.append((self.row - 1, self.col))

        if self.row <= 17:
            coords.append((self.row + 1, self.col))

        if self.col >= 1:
            coords.append((self.row, self.col - 1))

        if self.col <= 17:
            coords.append((self.row, self.col + 1))

        return coords

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col

    @property
    def color(self):
        return self._color
