from abc import ABC, abstractmethod
from copy import copy
from typing import Optional, Iterable, Union, Tuple

import cv2
import numpy as np
from numpy import array, ndarray

from game_state import GameState, Board
from piece import Piece, Color

CELL_COUNT = 18

class Image:
    """
    Each instance represents a numpy array as an rgb image
    """
    _bgra_array: ndarray

    def __init__(self, bgra_array: ndarray):
        self._bgra_array = bgra_array
        self._height = bgra_array.shape[0]
        self._width = bgra_array.shape[1]

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    @property
    def bgra_array(self) -> ndarray:
        return self._bgra_array

    def __copy__(self):
        return Image(np.copy(self._bgra_array))

    @staticmethod
    def place_on_top(bigger: 'Image', smaller: 'Image', upper_left: Tuple[int, int]) -> 'Image':
        """
        This function gives shit about alpha channel, not like opencv which doesn't give a damn.

        :param bigger:
        :param smaller:
        :param upper_left: row, col
        :return:
        """
        row, col = upper_left
        bigger_array = bigger._bgra_array
        smaller_array = smaller._bgra_array

        #
        max_row, max_col = row + smaller.height, col + smaller.width
        bigger_alpha = bigger_array[row:max_row, col:max_col, 3]
        smaller_alpha = smaller._bgra_array[:, :, 3]
        smaller_weight = smaller_alpha / 255

        # smaller_weight = smaller_alpha / (smaller_alpha.astype(np.uint16) + bigger_alpha.astype(np.uint16))
        bigger_weight = 1 - smaller_weight
        for channel in range(3):
            bigger_array[row:max_row, col:max_col, channel] = bigger_array[row:max_row, col:max_col,
                                                              channel] * bigger_weight + smaller_array[:, :,
                                                                                         channel] * smaller_weight

        bigger_array[row:max_row, col:max_col, 3] = (smaller_alpha + bigger_alpha * bigger_weight).astype(np.uint8)

        return Image(bigger_array)


class _Drawer(ABC):
    """
    Each instance can draw a certain Image
    """

    @abstractmethod
    def draw(self, *args, **kwargs) -> Image:
        ...


class _StaticImageDrawer(_Drawer, ABC):
    """
    A instance only draws one image that won't change
    """
    _cache: Optional[Image]

    def __init__(self):
        self._cache = self._image_cache()

    @abstractmethod
    def _image_cache(self) -> Image:
        ...

    def draw(self) -> Image:
        return self._cache


class _EmptyBoardDrawer(_StaticImageDrawer):
    BOARD_COLOR_BGR = (66, 200, 245)  # yellow

    def __init__(self, board_size: int, padding_ratio: float):
        """
        An instance draws an empty 19x19 board with grids.

        :param board_size: length of the square board in pixels
        """
        self._board_size = board_size
        self._cell_size = board_size // CELL_COUNT
        self._padding_ratio = padding_ratio

        self._padding_size = int(self._padding_ratio * self._board_size)

        super().__init__()

    @property
    def padding_size(self) -> int:
        return self._padding_size

    @property
    def board_size(self):
        return self._board_size

    @property
    def cell_size(self):
        return self._cell_size

    def _image_cache(self) -> Image:
        padding_size = self.padding_size

        grid_seps = np.linspace(padding_size + 1, self._board_size - 1 - padding_size, 19, dtype=int)
        blank_board = np.zeros((self._board_size, self._board_size, 4), dtype=np.uint8)

        for ind, color_val in enumerate(self.BOARD_COLOR_BGR):
            blank_board[:, :, ind] = color_val

        # grids
        blank_board[grid_seps, padding_size + 1:self._board_size - padding_size, :3] = 0
        blank_board[padding_size + 1:self._board_size - padding_size, grid_seps, :3] = 0

        # transparency
        blank_board[:, :, 3] = 255

        return Image(blank_board)


class _PieceDrawer(_StaticImageDrawer):

    def __init__(self, color: Color, piece_size: int):
        """

        :param color:
        :param piece_size: the diameter of the piece
        """
        self._color = color
        self._piece_size = piece_size

        super().__init__()

    def _image_cache(self) -> Image:
        piece_size = self._piece_size
        piece_radius = (self._piece_size - 2) // 2

        if self._color is Color.WHITE:
            bgra = (255, 255, 255, 255)
        else:
            bgra = (0, 0, 0, 255)

        transparent_square = np.zeros((piece_size, piece_size, 4), dtype=np.uint8)
        cv2.circle(transparent_square, (piece_radius, piece_radius), piece_radius, bgra, thickness=-1,
                   lineType=cv2.LINE_AA)
        return Image(transparent_square)


class BoardDrawer(_Drawer):
    _last_board_image: Optional[Image]

    # full piece size / full cell size
    CELL_PIECE_SIZE_RATIO = .8

    # SINGLE side padding / board size
    BOARD_PADDING_RATIO = .05

    def __init__(self, board_size: int):
        """

        :param board_size: the size of the board in pixels
        """
        self._empty_board_drawer = _EmptyBoardDrawer(board_size, self.BOARD_PADDING_RATIO)
        piece_size = int(self._empty_board_drawer.cell_size * self.CELL_PIECE_SIZE_RATIO)
        self._white_piece_drawer = _PieceDrawer(Color.WHITE, piece_size)
        self._black_piece_drawer = _PieceDrawer(Color.BLACK, piece_size)

        board_size = self._empty_board_drawer.board_size

        board_padding_size = self._empty_board_drawer.padding_size

        self._board_rc_to_image_rc = {
            (r, c): (int(board_padding_size + r * board_size * (1 - self.BOARD_PADDING_RATIO*2) / CELL_COUNT - piece_size / 2),
                     int(board_padding_size + c * board_size * (1 - self.BOARD_PADDING_RATIO*2) / CELL_COUNT - piece_size / 2))
            for r in range(CELL_COUNT+1) for c in range(CELL_COUNT+1)}

    def draw(self, board: Board) -> Image:
        board_image = copy(self._empty_board_drawer.draw())

        for piece in board.pieces:
            piece_image_coords = self._board_rc_to_image_rc[piece.row, piece.col]
            if piece.color is Color.WHITE:
                Image.place_on_top(board_image, self._white_piece_drawer.draw(), piece_image_coords)
            if piece.color is Color.BLACK:
                Image.place_on_top(board_image, self._black_piece_drawer.draw(), piece_image_coords)

        return board_image
