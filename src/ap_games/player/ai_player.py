from __future__ import annotations

from itertools import cycle
import random
from random import choice as random_choice
from typing import TYPE_CHECKING

from ap_games.gameboard.gameboard import SquareGameboard

# from ap_games.log import log
from ap_games.player.player import Player
from ap_games.ap_types import Step
from ap_games.player.player import TEST_MODE

if TYPE_CHECKING:
    from typing import ClassVar
    from typing import Dict
    from typing import Iterator
    from typing import List
    from typing import Optional
    from typing import Tuple
    from ap_games.ap_types import Coordinate

__ALL__ = ['AIPlayer']

if TEST_MODE:
    random.seed(123)


class AIPlayer(Player):
    max_depth: ClassVar[Dict[str, int]] = {
        "easy": 0,
        "medium": 2,
        "hard": 4,
    }

    def _get_terminal_score(
        self, *, depth: int, gameboard: SquareGameboard, player: Player
    ) -> Tuple[int, int]:
        """Return ``score`` and ``percentage`` of terminal state."""

        score: int
        """In the minimax algorithm, it doesn't matter how many ways
        to win AI at the end of the game. Therefore, the AI
        "stops fighting" and​is not trying to "steal" one of them.
        With the variable ``percentage``, the case with two
        possible steps to lose are worse than one.
        This is especially important if the "depth" of analysis is
        limited.

        Run example below with and without ``percentage`` once or twice:
        TicTacToe(surface="X_OXX_O__", player_types=("easy", "hard")).play()

        hint: "hard" select cell randomly from all empty cells and
        can lose to "easy" without ``percentage``."""
        percentage: int
        """In the minimax algorithm, it doesn't matter when you lose:
        now or later. Therefore, the AI "stops fighting" if it
        in any case loses the next steps, regardless of how it takes
        the step now. In this case, the AI considers that all the
        steps are the same bad, but this is wrong.
        Because the adversary can make a mistake, and adding the
        variable ``factor`` allows the AI to use a possible
        adversary errors in the future.
        With the ``factor``, losing now is worse than losing later.
        Therefore, the AI is trying not to "give up" now and wait
        for better chances in the future.
        This is especially important if the "depth" of analysis is
        limited.

        Run example below with and without ``factor`` once or twice:
        TicTacToe(surface="X_OX_____", player_types=("easy", "hard")).play()

        hint: "hard" select cell randomly from all empty cells and
        can lose to "easy" without ``factor``."""
        factor: int = 1

        if self.game.get_status(gameboard=gameboard, player=player).active:
            if depth < self.max_depth[self.type]:
                _, score, percentage = self._minimax(
                    depth=depth + 1, gameboard=gameboard, player=player
                )
            else:
                score = self.game.get_score(gameboard=gameboard, player=self)
                percentage = 100
        else:
            factor *= self.max_depth[self.type] + 1 - depth
            score = self.game.get_score(gameboard=gameboard, player=self)
            percentage = 100
        return score * factor, percentage

    def _get_next_player(self, current_player: Player) -> Player:
        players_cycle: Iterator[Player] = cycle(self.game.players)
        while next(players_cycle) != current_player:
            pass
        return next(players_cycle)

    def _extract_desired_steps(
        self, depth: int, steps: List[Step], player: Player
    ) -> List[Step]:
        if player == self:
            score_func = max
        else:
            score_func = min

        desired_score: int = score_func(step.score for step in steps)
        desired_steps: List[Step] = [
            step for step in steps if step.score == desired_score
        ]
        # log.debug(
        #     "\t" * depth + f"desired score steps ({score_func}) -> {desired_steps}"
        # )
        return desired_steps

    def _extract_most_likely_steps(
        self, depth: int, steps: List[Step], player: Player
    ) -> List[Step]:
        # Note: all Steps on this stage have the same score
        desired_score: int = steps[0].score

        if (desired_score >= 0 and player == self) or (
            desired_score < 0 and player != self
        ):
            # maximize the probability of self own winning or adversary
            # losing
            percentage_func = max
        else:
            percentage_func = min
        desired_percentage: int = percentage_func(step.percentage for step in steps)
        most_likely_steps: List[Step] = [
            step for step in steps if step.percentage == desired_percentage
        ]
        # log.debug(
        #     "\t" * depth
        #     + f"desired percentage steps ({percentage_func}) -> "
        #     + str(most_likely_steps)
        # )
        return most_likely_steps

    def _minimax(
        self,
        *,
        depth: int,
        gameboard: Optional[SquareGameboard] = None,
        player: Optional[Player] = None,
    ) -> Step:
        """Algorithm:

        1. Go through available spots on the board;
        2. Return a value (score) if a terminal state is found
           (:meth:`._get_terminal_score`);
        3. or call the minimax function on each available spot
           (recursion).
        4. Evaluate returning values from function calls
           (:meth:`._extract_desired_steps` and
           :meth:`._extract_most_likely_steps`);
        5. And return the best value (Step).

        TODO: swap the first and second item.
         In the current implementation, there may be an error if
         running the method with the ``gameboard`` without the available
         steps.

        """
        if gameboard is None:
            gameboard = self.game.gameboard
        if player is None:
            player = self

        steps: List[Step] = list()
        for coordinate in player.game.available_steps(
            gameboard=gameboard, player=player
        ):
            fake_gameboard: SquareGameboard = gameboard.copy
            self.game.step(coordinate, gameboard=fake_gameboard, player=player)

            # log.debug("\n " + ("\t" * depth) + f"[{player.label}] {coordinate}")
            # log.debug(
            #     "\n".join(
            #         '\t' * depth + line for line in str(fake_gameboard).split("\n")
            #     )
            # )

            next_player = self._get_next_player(current_player=player)

            terminal_score, percentage = self._get_terminal_score(
                depth=depth, gameboard=fake_gameboard, player=next_player
            )
            steps.append(Step(coordinate, terminal_score, percentage))

        desired_steps: List[Step] = self._extract_desired_steps(
            depth=depth, steps=steps, player=player
        )

        most_likely_steps: List[Step] = self._extract_most_likely_steps(
            depth=depth, steps=desired_steps, player=player
        )

        step = random_choice(most_likely_steps)
        # compute and replace ``percentage`` in the selected step
        step = step._replace(percentage=int(len(desired_steps) / len(steps) * 100))
        # log.debug("\t" * depth + f"selected step: {step}")

        return step

    def go(self) -> Coordinate:
        print(f'Making move level "{self.type}" [{self.label}]')

        depth: int = 0
        if depth < self.max_depth[self.type]:
            return self._minimax(depth=depth + 1).coordinate
        return self._random_coordinate()