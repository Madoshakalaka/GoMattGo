import enum
import math
from abc import ABC
from copy import copy
from typing import Union, Iterable, List, Set, Any, Tuple

from piece import Color, Piece


class PositionState(enum.Enum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2


class Group:
    def __init__(self, pieces: Set[Piece], liberties: Set[Tuple[int, int]]):
        self._pieces = pieces
        self.liberties = liberties

    @property
    def liberal(self):
        return len(self.liberties) != 0

    @property
    def pieces(self):
        return self._pieces


class Board:
    _board: List[List[PositionState]]

    def __init__(self):
        self._board = [[PositionState.EMPTY] * 19 for _ in range(19)]

    @property
    def empty_positions(self) -> Iterable[Tuple[int, int]]:
        for r_ind, row in enumerate(self._board):
            for col_ind, ps in enumerate(row):
                if ps is PositionState.EMPTY:
                    yield r_ind, col_ind

    def set_cell(self, r: int, c: int, cell_state: PositionState):
        self._board[r][c] = cell_state

    def remove_group(self, group: Group):
        for piece in group.pieces:
            self._board[piece.row][piece.col] = PositionState.EMPTY

    def __copy__(self):
        b = Board()
        b._board = [list(r) for r in self._board]
        return b

    def get_groups(self, color: Color) -> List[Group]:

        raw_groups: List[Set[Piece]] = []

        added_pieces: Set[Piece] = set()

        all_pieces = set([p for p in self.pieces if p.color is color])

        for piece in all_pieces:
            if not (piece in added_pieces):
                # now we build this group starting from this piece
                group = {piece}
                self.build_group(piece, all_pieces - group, group)

                added_pieces |= group
                raw_groups.append(group)

        return [Group(raw_group, self.count_liberties(raw_group)) for raw_group in raw_groups]

    def count_liberties(self, group: Set[Piece]) -> Set[Tuple[int, int]]:
        liberties = set()
        for piece in group:
            for row, col in piece.adjacent_coordinates:
                if self._board[row][col] is PositionState.EMPTY:
                    liberties.add((row, col))
        return liberties

    @staticmethod
    def build_group(piece, considered_pieces, group):

        all_adj = Board.find_adjacent_pieces(piece, considered_pieces - group)


        for adj in all_adj:
            group.add(adj)
            Board.build_group(adj, considered_pieces - group, group)


    @staticmethod
    def find_adjacent_pieces(p: Piece, pieces: Iterable[Piece]):
        all_adj = []
        for some_p in pieces:
            if (abs(p.row - some_p.row) == 1 and p.col == some_p.col) and (
                    abs(p.col - some_p.col) == 1 and p.row == some_p.row):
                all_adj.append(p)
        return all_adj

    def __hash__(self):

        # it enables us to check kos efficiently
        return hash(''.join([str(x) for row in self._board for x in row]))

    def is_position_occupied(self, r: int, c: int):
        return not (self._board[r][c] is PositionState.EMPTY)

    @property
    def pieces(self) -> Iterable[Piece]:
        for r_ind, row in enumerate(self._board):
            for c_ind, position_state in enumerate(row):
                if position_state is PositionState.WHITE:
                    yield Piece(r_ind, c_ind, Color.WHITE)
                elif position_state is PositionState.BLACK:
                    yield Piece(r_ind, c_ind, Color.BLACK)


class Action(ABC):
    """
    All things a player can do, namely move and pass etc. (surrender?)
    """
    ...


class Pass(Action):

    def __repr__(self):
        return "Pass"


class Move(Action):
    def __init__(self, r: int, c: int):
        self._r = r
        self._c = c

    @property
    def r(self):
        return self._r

    @property
    def c(self):
        return self._c

    def __repr__(self):
        return f"Move {self.r} {self.c}"


class IllegalMoveError(Exception):
    ...


COLOR_REVERSE = {Color.WHITE: Color.BLACK, Color.BLACK: Color.WHITE, PositionState.WHITE: PositionState.BLACK,
                 PositionState.BLACK: PositionState.WHITE}


class GameState:
    _past_boards: Set[Board]
    _board: Board

    def __init__(self):
        self._board = Board()
        self._turn = Color.BLACK

        self._num_of_passes = 0

        self._past_boards = set()

    @property
    def board(self):
        return self._board

    @property
    def is_ended(self) -> bool:
        # check if the game has ended
        return self._num_of_passes == 2

    def count_scores(self) -> Tuple[int, int]:
        """
        black score + white score
        """
        # todo: count scores
        pass

    @staticmethod
    def fill_new_piece(board: Board, move: Move, turn: Color):
        if turn is Color.BLACK:
            ps = PositionState.BLACK
        else:
            ps = PositionState.WHITE

        board.set_cell(move.r, move.c, ps)

    def update(self, action: Action):
        """

        :raise IllegalMoveError
        """

        other_color = COLOR_REVERSE[self._turn]

        if isinstance(action, Pass):
            self._num_of_passes += 1
        elif isinstance(action, Move):
            if self._board.is_position_occupied(action.r, action.c):
                raise IllegalMoveError

            if self.detect_ko(action):
                raise IllegalMoveError

            self.fill_new_piece(self._board, action, self._turn)

            self.remove_components(other_color)
            self.remove_components(self._turn)

        else:
            raise NotImplementedError

        self._past_boards.add(copy(self._board))
        self._turn = other_color

    def detect_ko(self, move: Move):
        """
        :param move: move where position is empty
        :return:
        """
        hypothetical_board = copy(self._board)
        self.fill_new_piece(hypothetical_board, move, self._turn)
        other_color = COLOR_REVERSE[self._turn]
        self._remove_components(hypothetical_board, other_color)
        self._remove_components(hypothetical_board, self._turn)
        if hypothetical_board in self._past_boards:
            return True

    @staticmethod
    def _remove_components(board: Board, color: Color):
        for group in board.get_groups(color):
            if not group.liberal:
                board.remove_group(group)

    def remove_components(self, color: Color):
        """
        remove components with no liberties
        """
        self._remove_components(self._board, color)
