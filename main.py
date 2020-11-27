import cv2

from game_state import GameState, Action, Move, Pass
from drawer import BoardDrawer
import random

class Game:

    def __init__(self):
        self._game_state = GameState()

    def start(self):
        """
        this function blocks until game ends
        """
        drawer = BoardDrawer(500)
        game_state = self._game_state

        bot = RandBot(game_state)

        while not game_state.is_ended:

            cv2.imshow("GoMattGo", drawer.draw(game_state.board).bgra_array)
            cv2.waitKey(1)

            action = bot.decide()
            print(f"bot decides to: {action}")
            game_state.update(action)




class RandBot:
    def __init__(self, game_state: GameState):
        self._game_state = game_state

    def decide(self) -> Action:

        possible_coords = list(self._game_state.board.empty_positions)

        random.shuffle(possible_coords)

        for coords in possible_coords:
            move = Move(coords[0], coords[1])
            if self._game_state.detect_ko(move):
                continue
            else:
                return move

        return Pass()


if __name__ == '__main__':
    g = Game()
    g.start()
