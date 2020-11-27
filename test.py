"""
Various tests, some visual (requires pressing ESC manually)
"""
from typing import Callable

import cv2
import pytest

from drawer import Image, _EmptyBoardDrawer, _PieceDrawer, BoardDrawer
from game_state import Board, PositionState
from piece import Color


@pytest.fixture
def board_a() -> Board:
    b = Board()
    b.set_cell(0, 0, PositionState.WHITE)
    b.set_cell(0, 10, PositionState.BLACK)
    b.set_cell(13, 8, PositionState.WHITE)
    return b



def visual_test(prompt: str, image: Image):
    """
    press any key except f to pass the test
    """

    cv2.imshow(prompt + " Press f to fail the test", image.bgra_array)
    cv2.imwrite("test.png", image.bgra_array)
    if cv2.waitKey() == ord('f'):
        pytest.fail("visual test failed")


def test_blank_drawer():

    visual_test("Do you see an empty board with grids?", _EmptyBoardDrawer(500).draw())

def test_piece_drawer():
    visual_test("Do you see a solid white circular piece?", _PieceDrawer(Color.WHITE, 50).draw())


def test_draw_board(board_a):
    drawer = BoardDrawer(500)
    visual_test("Do you see a board with some pieces?", drawer.draw(board_a))

# todo: maybe never...test using specifically constructed CacheableDrawer class
# def test_caching():
#
#     repeat = 3000
#
#     without_cache_time = timeit(lambda: EmptyBoardDrawer(500).draw(), number=repeat)
#     d = EmptyBoardDrawer(500)
#     with_cache_time = timeit(lambda: d.draw(), number=3000)
#
#     print(without_cache_time,with_cache_time)
