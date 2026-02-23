"""
Battleship – main entry point.

Game modes
----------
1. Human vs Simple Reflex Agent
2. Human vs Goal-Based Agent
3. AI vs AI simulation (Simple Reflex vs Goal-Based) with win statistics
"""

from battleship import Board, Game, BOARD_SIZE, SHIPS, HIT, MISS
from agents import SimpleReflexAgent, GoalBasedAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_boards(my_board: Board, enemy_view: Board, my_label: str, enemy_label: str):
    """Print side-by-side: player's own board and their view of the enemy."""
    my_lines = my_board.display().splitlines()
    enemy_lines = enemy_view.display_opponent_view().splitlines()
    print(f"\n{'Your Board':^23}     {'Enemy Board (your shots)':^23}")
    for ml, el in zip(my_lines, enemy_lines):
        print(f"{ml:<23}     {el}")
    print()


def _get_human_shot(board: Board) -> tuple[int, int]:
    """Prompt the human for a valid (row, col) that hasn't been tried."""
    while True:
        try:
            raw = input("Enter your shot as 'row col' (0-9): ").strip()
            parts = raw.split()
            if len(parts) != 2:
                raise ValueError
            row, col = int(parts[0]), int(parts[1])
            if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                print(f"  ✗ Values must be between 0 and {BOARD_SIZE - 1}.")
                continue
            if board.opponent_view[row][col] != ".":
                print("  ✗ You already shot there. Try again.")
                continue
            return row, col
        except ValueError:
            print("  ✗ Invalid input. Enter two numbers separated by a space.")


def _place_ships_human(board: Board):
    """Let the human manually place all ships, or place them randomly."""
    choice = input("Place your ships manually? (y/n, default n): ").strip().lower()
    if choice != "y":
        board.place_ships_randomly()
        print("  Ships placed randomly.")
        print(board.display())
        return

    for name, size in SHIPS:
        print(f"\nPlacing {name} (size {size})")
        print(board.display())
        while True:
            try:
                raw = input(f"  Enter 'row col h/v' for {name}: ").strip().split()
                if len(raw) != 3:
                    raise ValueError
                row, col, orientation = int(raw[0]), int(raw[1]), raw[2].lower()
                if orientation not in ("h", "v"):
                    raise ValueError
                horizontal = orientation == "h"
                if board.place_ship(name, size, row, col, horizontal):
                    print(f"  ✓ {name} placed.")
                    break
                else:
                    print("  ✗ Invalid position (out of bounds or overlapping). Try again.")
            except (ValueError, IndexError):
                print("  ✗ Invalid input. Use format: row col h/v  (e.g. 3 4 h)")


# ---------------------------------------------------------------------------
# Game runners
# ---------------------------------------------------------------------------

def play_human_vs_ai(ai_type: str = "reflex"):
    """Human vs one of the AI agents."""
    print("\n" + "=" * 50)
    if ai_type == "reflex":
        agent = SimpleReflexAgent()
    else:
        agent = GoalBasedAgent()
    print(f"  Human vs {agent.name}")
    print("=" * 50)

    # Set up boards
    human_board = Board()
    ai_board = Board()

    print("\n--- Place your ships ---")
    _place_ships_human(human_board)
    ai_board.place_ships_randomly()

    game = Game(human_board, ai_board)
    # Player 0 = human (attacks ai_board), Player 1 = AI (attacks human_board)
    game.current = 0

    while not game.is_over():
        if game.current == 0:
            # Human's turn
            print("\n--- Your turn ---")
            _print_boards(human_board, ai_board, "You", agent.name)
            row, col = _get_human_shot(ai_board)
            result = game.shoot(row, col)
            print(f"  → {'HIT! 💥' if result == 'hit' else 'Miss.'}")
            if ai_board.all_ships_sunk():
                break
        else:
            # AI's turn
            row, col = agent.choose_shot()
            result = game.shoot(row, col)
            agent.update(row, col, result)
            mark = "HIT 💥" if result == "hit" else "miss"
            print(f"\n--- {agent.name}'s turn: shot ({row},{col}) → {mark} ---")
            if human_board.all_ships_sunk():
                break

        game.next_turn()

    # Result
    winner_idx = game.winner()
    print("\n" + "=" * 50)
    if winner_idx == 0:
        print("  🏆 YOU WIN!")
    else:
        print(f"  {agent.name} wins!")
    print("=" * 50)
    print("\nFinal boards:")
    print(f"\n{agent.name}'s board (revealed):")
    print(ai_board.display())
    print("\nYour board:")
    print(human_board.display())


def simulate_ai_vs_ai(num_games: int = 100, verbose: bool = False) -> dict[str, int]:
    """
    Simulate AI vs AI games and return win statistics.

    Returns a dict: {'Simple Reflex Agent': N, 'Goal-Based Agent': M}
    """
    wins: dict[str, int] = {
        SimpleReflexAgent.NAME: 0,
        GoalBasedAgent.NAME: 0,
    }

    for game_num in range(1, num_games + 1):
        reflex_board = Board()
        goal_board = Board()
        reflex_board.place_ships_randomly()
        goal_board.place_ships_randomly()

        reflex_agent = SimpleReflexAgent()
        goal_agent = GoalBasedAgent()

        # Player 0 = Reflex (attacks goal_board)
        # Player 1 = Goal   (attacks reflex_board)
        game = Game(reflex_board, goal_board)
        game.current = 0

        while not game.is_over():
            if game.current == 0:
                row, col = reflex_agent.choose_shot()
                result = game.shoot(row, col)
                reflex_agent.update(row, col, result)
            else:
                row, col = goal_agent.choose_shot()
                result = game.shoot(row, col)
                goal_agent.update(row, col, result)
            game.next_turn()

        winner_idx = game.winner()
        if winner_idx == 0:
            winner_name = SimpleReflexAgent.NAME
        else:
            winner_name = GoalBasedAgent.NAME
        wins[winner_name] += 1

        if verbose:
            print(f"  Game {game_num:>4}: {winner_name} wins")

    return wins


def run_ai_vs_ai_mode():
    """Interactive wrapper for the AI vs AI simulation."""
    print("\n" + "=" * 50)
    print("  AI vs AI Simulation")
    print("=" * 50)

    while True:
        try:
            num_games = int(input("How many games to simulate? (default 100): ").strip() or "100")
            if num_games < 1:
                raise ValueError
            break
        except ValueError:
            print("  ✗ Please enter a positive integer.")

    verbose_input = input("Show each game result? (y/n, default n): ").strip().lower()
    verbose = verbose_input == "y"

    print(f"\nSimulating {num_games} games…\n")
    wins = simulate_ai_vs_ai(num_games, verbose=verbose)

    total = sum(wins.values())
    print("\n" + "=" * 50)
    print("  RESULTS")
    print("=" * 50)
    for agent_name, count in wins.items():
        pct = (count / total * 100) if total else 0
        print(f"  {agent_name:<30} {count:>5} wins  ({pct:.1f}%)")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def main():
    print("\n" + "#" * 50)
    print("#" + " " * 16 + "BATTLESHIP" + " " * 22 + "#")
    print("#" * 50)

    while True:
        print("\nMain Menu:")
        print("  1. Human vs Simple Reflex Agent")
        print("  2. Human vs Goal-Based Agent")
        print("  3. AI vs AI simulation (with statistics)")
        print("  4. Quit")

        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            play_human_vs_ai(ai_type="reflex")
        elif choice == "2":
            play_human_vs_ai(ai_type="goal")
        elif choice == "3":
            run_ai_vs_ai_mode()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("  ✗ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
