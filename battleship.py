"""Core Battleship game logic: Board, Ship, and Game classes."""

import random

BOARD_SIZE = 10
SHIPS = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

HIT = "X"
MISS = "O"
EMPTY = "."
SHIP = "S"


class Ship:
    """Represents a single ship on the board."""

    def __init__(self, name: str, size: int, positions: list[tuple[int, int]]):
        self.name = name
        self.size = size
        self.positions = set(positions)
        self.hits: set[tuple[int, int]] = set()

    def receive_shot(self, row: int, col: int) -> bool:
        """Register a shot. Returns True if it hit this ship."""
        if (row, col) in self.positions:
            self.hits.add((row, col))
            return True
        return False

    def is_sunk(self) -> bool:
        return self.hits == self.positions


class Board:
    """10x10 Battleship board that manages ships and shot tracking."""

    def __init__(self):
        self.size = BOARD_SIZE
        self.ships: list[Ship] = []
        # grid stores EMPTY, SHIP, HIT, or MISS
        self.grid: list[list[str]] = [[EMPTY] * self.size for _ in range(self.size)]
        # opponent_view stores only what an attacker can see (HIT / MISS / EMPTY)
        self.opponent_view: list[list[str]] = [[EMPTY] * self.size for _ in range(self.size)]

    # ------------------------------------------------------------------
    # Ship placement
    # ------------------------------------------------------------------

    def place_ship(self, ship_name: str, size: int, row: int, col: int, horizontal: bool) -> bool:
        """
        Try to place a ship. Returns True on success, False if the placement
        is invalid (out of bounds or overlapping).
        """
        positions = []
        for i in range(size):
            r = row + (0 if horizontal else i)
            c = col + (i if horizontal else 0)
            if not self._in_bounds(r, c) or self.grid[r][c] == SHIP:
                return False
            positions.append((r, c))
        ship = Ship(ship_name, size, positions)
        self.ships.append(ship)
        for r, c in positions:
            self.grid[r][c] = SHIP
        return True

    def place_ships_randomly(self):
        """Place all standard ships at random valid positions."""
        for name, size in SHIPS:
            placed = False
            while not placed:
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - 1)
                horizontal = random.choice([True, False])
                placed = self.place_ship(name, size, row, col, horizontal)

    # ------------------------------------------------------------------
    # Shooting
    # ------------------------------------------------------------------

    def receive_shot(self, row: int, col: int) -> str:
        """
        Process an incoming shot. Returns 'hit', 'miss', or 'already_shot'.
        Updates both the internal grid and the opponent_view.
        """
        if self.opponent_view[row][col] != EMPTY:
            return "already_shot"
        for ship in self.ships:
            if ship.receive_shot(row, col):
                self.grid[row][col] = HIT
                self.opponent_view[row][col] = HIT
                return "hit"
        self.grid[row][col] = MISS
        self.opponent_view[row][col] = MISS
        return "miss"

    def all_ships_sunk(self) -> bool:
        return all(ship.is_sunk() for ship in self.ships)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display(self, hide_ships: bool = False) -> str:
        """Return a printable string of the board."""
        col_header = "  " + " ".join(str(i) for i in range(self.size))
        rows = [col_header]
        for r in range(self.size):
            row_cells = []
            for c in range(self.size):
                cell = self.grid[r][c]
                if hide_ships and cell == SHIP:
                    row_cells.append(EMPTY)
                else:
                    row_cells.append(cell)
            rows.append(f"{r} " + " ".join(row_cells))
        return "\n".join(rows)

    def display_opponent_view(self) -> str:
        """Return a printable string of what the attacker can see."""
        col_header = "  " + " ".join(str(i) for i in range(self.size))
        rows = [col_header]
        for r in range(self.size):
            rows.append(f"{r} " + " ".join(self.opponent_view[r]))
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size


class Game:
    """
    Manages a single Battleship game between two players.

    Each player has a Board. Players take turns shooting at the opponent's
    Board. A 'player' can be a human (providing input externally) or an AI
    agent.
    """

    def __init__(self, player1_board: Board, player2_board: Board):
        self.boards = [player1_board, player2_board]
        self.current = 0  # index of the player whose turn it is

    @property
    def active_board(self) -> Board:
        """The board of the player who is currently attacking."""
        return self.boards[self.current]

    @property
    def target_board(self) -> Board:
        """The board being attacked this turn."""
        return self.boards[1 - self.current]

    def shoot(self, row: int, col: int) -> str:
        """
        Fire at (row, col) on the target board.
        Returns 'hit', 'miss', or 'already_shot'.
        Does NOT switch turns – the caller decides whether to advance.
        """
        return self.target_board.receive_shot(row, col)

    def next_turn(self):
        """Advance to the next player's turn."""
        self.current = 1 - self.current

    def is_over(self) -> bool:
        return any(b.all_ships_sunk() for b in self.boards)

    def winner(self) -> int | None:
        """Return 0 or 1 (index of winner), or None if not over."""
        for i, board in enumerate(self.boards):
            if board.all_ships_sunk():
                return 1 - i  # the other player won
        return None
