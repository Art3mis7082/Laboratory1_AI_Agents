"""
Battleship AI agents.

SimpleReflexAgent
-----------------
A **simple reflex agent**: it reacts only to the immediate percept (the
result of its last shot) with a fixed rule – always pick a random cell
from the cells that have not been shot at yet. It has no memory of *why*
it won or lost, and carries no internal model of where the enemy ships
might be.

GoalBasedAgent
--------------
A **goal-based agent**: its explicit goal is to sink every enemy ship. It
keeps an internal model (which cells are unknown, hit, or missed) and uses
a two-phase *hunt-and-target* strategy to work toward that goal:
  • Hunt phase  – fire at random unexplored cells to locate a ship.
  • Target phase – once a hit is recorded, systematically fire at
                   adjacent cells to finish sinking the ship.
"""

import random
from battleship import BOARD_SIZE, HIT, MISS, EMPTY


class SimpleReflexAgent:
    """
    Simple reflex agent for Battleship.

    Decision rule: given the set of untried cells, pick one at random.
    The only 'reflex' is that it never shoots the same cell twice, which
    is encoded as a direct response to the percept: if the chosen cell
    was already shot, skip it (handled by maintaining the untried set).
    """

    NAME = "Simple Reflex Agent"

    def __init__(self):
        self.name = self.NAME
        # All cells are untried at the start
        self._untried: list[tuple[int, int]] = [
            (r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
        ]
        random.shuffle(self._untried)

    def choose_shot(self) -> tuple[int, int]:
        """Return the next cell to shoot at."""
        return self._untried.pop()

    def update(self, row: int, col: int, result: str):
        """
        Receive the result of a shot ('hit' or 'miss').
        The simple reflex agent ignores results beyond removing the cell
        from the untried list (already done by choose_shot).
        """
        pass  # No memory or strategy update needed – pure reflex


class GoalBasedAgent:
    """
    Goal-based agent for Battleship.

    Goal: sink all enemy ships.

    Internal model:
      - A set of unexplored cells (hunt candidates).
      - A queue of adjacent cells to probe after scoring a hit (target
        queue). As long as the target queue is non-empty the agent is in
        *target phase*; otherwise it is in *hunt phase*.

    Strategy:
      Hunt phase  → fire at a random unexplored cell.
      Target phase → fire at the first cell in the target queue that has
                     not yet been tried.
    """

    NAME = "Goal-Based Agent"

    def __init__(self):
        self.name = self.NAME
        self._untried: set[tuple[int, int]] = {
            (r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
        }
        self._target_queue: list[tuple[int, int]] = []
        self._shot_cells: set[tuple[int, int]] = set()

    def choose_shot(self) -> tuple[int, int]:
        """Return the next cell to shoot at based on current phase."""
        # Target phase: work through adjacent cells of previous hits
        while self._target_queue:
            candidate = self._target_queue.pop(0)
            if candidate in self._untried:
                return candidate

        # Hunt phase: pick a random unexplored cell
        cell = random.choice(list(self._untried))
        return cell

    def update(self, row: int, col: int, result: str):
        """
        Update internal model with the result of the last shot.

        On a hit: enqueue the four neighbours so we can target the ship.
        On a miss: nothing extra – the cell is simply marked as tried.
        """
        self._untried.discard((row, col))
        self._shot_cells.add((row, col))

        if result == "hit":
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < BOARD_SIZE
                    and 0 <= nc < BOARD_SIZE
                    and (nr, nc) not in self._shot_cells
                    and (nr, nc) not in self._target_queue
                ):
                    self._target_queue.append((nr, nc))
