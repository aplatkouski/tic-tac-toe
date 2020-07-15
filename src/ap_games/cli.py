from __future__ import annotations

from typing import TYPE_CHECKING
from ap_games.game.reversi import Reversi
from ap_games.game.tictactoe import TicTacToe

if TYPE_CHECKING:
    from typing import Type
    from ap_games.game.game_base import GameBase

__ALL__ = ['cli']


def cli(game_class: Type[GameBase] = TicTacToe) -> None:
    command: str = input("Input command: ")
    while command != "exit":
        parameters = command.split()
        if (
                len(parameters) == 3
                and parameters[0] == "start"
                and parameters[1] in game_class.supported_players
                and parameters[2] in game_class.supported_players
        ):
            game = game_class(player_types=(parameters[1], parameters[2]))
            game.play()
        else:
            print("Bad parameters!")
        command = input("Input command: ")


if __name__ == "__main__":
    choice: str = ""
    while choice != "exit":
        choice = input("Please choose the game:\n"
                       "\t0 - Tic-Tac-Toe;\n"
                       "\t1 - Reversi [by default].\n"
                       "Print 'exit' to exit the program.\n> ")
        if choice == "0":
            cli(game_class=TicTacToe)
        elif choice == "1":
            cli(game_class=Reversi)
