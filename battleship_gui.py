import pygame
import sys
from battleship import HumanPlayer, RandomAI, HunterAI, Board, SHIPS, GRID_SIZE, EMPTY, SHIP, HIT, MISS, SUNK

# ─────────────────────────────────────────────
#  Constants & Configuration
# ─────────────────────────────────────────────
CELL_SIZE = 40
MARGIN = 50
BOARD_WIDTH = GRID_SIZE * CELL_SIZE
WINDOW_WIDTH = (BOARD_WIDTH * 2) + (MARGIN * 3)
WINDOW_HEIGHT = BOARD_WIDTH + (MARGIN * 2) + 150

BG_COLOR = (30, 30, 40)
TEXT_COLOR = (220, 220, 220)
GRID_COLOR = (100, 100, 120)
GHOST_VALID = (50, 200, 80, 100)    # Translucent green
GHOST_INVALID = (220, 50, 50, 100)  # Translucent red

COLOR_MAP = {
    EMPTY: (20, 40, 80),
    SHIP: (50, 200, 80),
    HIT: (220, 50, 50),
    MISS: (150, 150, 150),
    SUNK: (139, 0, 0)
}

# ─────────────────────────────────────────────
#  UI Helpers
# ─────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = (70, 70, 90)
        self.hover_color = (100, 100, 120)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# ─────────────────────────────────────────────
#  Main Application State Machine
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
#  Main Application State Machine
# ─────────────────────────────────────────────
class BattleshipGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Battleship - AI Simulation Engine")
        self.clock = pygame.time.Clock()
        
        self.font_large = pygame.font.SysFont("consolas", 36, bold=True)
        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 16)

        self.state = "MENU"
        
        # Menu variables
        self.mode = "PvAI"     
        self.ai1_type = "Hunter" 
        self.ai2_type = "Random" 
        self.player1_name = "Player 1"
        self.player2_name = "AI 2"
        self.num_matches = "100" # Default n matches
        self.active_input = None  

        # Game variables
        self.p1 = None
        self.p2 = None
        self.turn = 0
        self.game_over = False
        self.status_msg = ""
        self.ai_delay_timer = 0
        
        # Simulation stats
        self.stats = {}

        # Placement variables
        self.ships_to_place = []
        self.is_horizontal = True

        self.setup_menu_buttons()

    def setup_menu_buttons(self):
        cx = WINDOW_WIDTH // 2
        self.btn_mode = Button(cx - 100, 100, 200, 40, f"Mode: {self.mode}", self.font)
        
        # Left column (Player 1)
        self.btn_ai1 = Button(cx - 220, 170, 200, 40, f"P1 AI: {self.ai1_type}", self.font)
        self.p1_rect = pygame.Rect(cx - 220, 240, 200, 40)
        
        # Right column (Player 2)
        self.btn_ai2 = Button(cx + 20, 170, 200, 40, f"P2 AI: {self.ai2_type}", self.font)
        self.p2_rect = pygame.Rect(cx + 20, 240, 200, 40)
        
        # Center bottom (N matches & Start)
        self.n_rect = pygame.Rect(cx - 100, 330, 200, 40)
        self.btn_start = Button(cx - 100, 410, 200, 50, "START", self.font_large)
        self.btn_menu = Button(cx - 100, 400, 200, 50, "BACK TO MENU", self.font)

    # ─── MENU STATE ──────────────────────────────────────
    def handle_menu_events(self, event):
        if self.btn_mode.is_clicked(event):
            self.mode = "AIvAI" if self.mode == "PvAI" else "PvAI"
            self.btn_mode.text = f"Mode: {self.mode}"
        
        if self.mode == "AIvAI" and self.btn_ai1.is_clicked(event):
            self.ai1_type = "Random" if self.ai1_type == "Hunter" else "Hunter"
            self.btn_ai1.text = f"P1 AI: {self.ai1_type}"

        if self.btn_ai2.is_clicked(event):
            self.ai2_type = "Random" if self.ai2_type == "Hunter" else "Hunter"
            self.btn_ai2.text = f"P2 AI: {self.ai2_type}"

        if self.btn_start.is_clicked(event):
            self.start_game_setup()

        # Handle text box selection
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.p1_rect.collidepoint(event.pos): self.active_input = "P1"
            elif self.p2_rect.collidepoint(event.pos): self.active_input = "P2"
            elif self.mode == "AIvAI" and self.n_rect.collidepoint(event.pos): self.active_input = "N"
            else: self.active_input = None

        # Handle typing
        if event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input == "P1": self.player1_name = self.player1_name[:-1]
                elif self.active_input == "P2": self.player2_name = self.player2_name[:-1]
                elif self.active_input == "N": self.num_matches = self.num_matches[:-1]
            elif event.unicode.isprintable():
                if self.active_input == "P1" and len(self.player1_name) < 12:
                    self.player1_name += event.unicode
                elif self.active_input == "P2" and len(self.player2_name) < 12:
                    self.player2_name += event.unicode
                elif self.active_input == "N" and event.unicode.isdigit() and len(self.num_matches) < 5:
                    self.num_matches += event.unicode # Only allow digits for matches

    def draw_menu(self):
        title = self.font_large.render("BATTLESHIP SETUP", True, (100, 200, 255))
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 50)))

        self.btn_mode.draw(self.screen)
        self.btn_ai2.draw(self.screen)
        
        if self.mode == "AIvAI":
            self.btn_ai1.draw(self.screen)
        
        # Draw Text Inputs (Helper function for cleaner code)
        self._draw_input_box(self.p1_rect, self.player1_name, "Player 1 Name:", self.active_input == "P1")
        self._draw_input_box(self.p2_rect, self.player2_name, "Player 2 Name:", self.active_input == "P2")
        
        if self.mode == "AIvAI":
            self._draw_input_box(self.n_rect, self.num_matches, "Number of Matches (n):", self.active_input == "N")

        self.btn_start.draw(self.screen)

    def _draw_input_box(self, rect, text, label, is_active):
        color = (100, 200, 255) if is_active else (200, 200, 200)
        pygame.draw.rect(self.screen, (50, 50, 70), rect)
        pygame.draw.rect(self.screen, color, rect, 2)
        txt_surf = self.font.render(text + ("|" if is_active else ""), True, TEXT_COLOR)
        self.screen.blit(txt_surf, (rect.x + 10, rect.y + 10))
        lbl_surf = self.font_small.render(label, True, TEXT_COLOR)
        self.screen.blit(lbl_surf, (rect.x, rect.y - 20))

    # ─── SETUP & PLACEMENT STATE ─────────────────────────
    def start_game_setup(self):
        n = int(self.num_matches) if self.num_matches else 1
        
        if self.mode == "AIvAI" and n > 1:
            self.state = "SIMULATING"
            self.run_simulation(n)
            return

        # Create P1
        if self.mode == "PvAI":
            self.p1 = HumanPlayer(self.player1_name)
            self.ships_to_place = SHIPS.copy()
            self.state = "PLACEMENT"
        else:
            AI1 = HunterAI if self.ai1_type == "Hunter" else RandomAI
            self.p1 = AI1(self.player1_name)
            self.p1.board.place_all_random()
            self.state = "PLAYING"

        # Create P2
        AI2 = HunterAI if self.ai2_type == "Hunter" else RandomAI
        self.p2 = AI2(self.player2_name)
        self.p2.board.place_all_random()

        self.turn = 0
        self.game_over = False
        self.status_msg = "Game Started!"

    def handle_placement_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.is_horizontal = not self.is_horizontal

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            board_x, board_y = MARGIN, MARGIN + 50
            
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE
                
                name, length = self.ships_to_place[0]
                if self.p1.board.can_place(col, row, length, self.is_horizontal):
                    self.p1.board.place_ship(name, col, row, length, self.is_horizontal)
                    self.ships_to_place.pop(0)
                    
                    if not self.ships_to_place:
                        self.state = "PLAYING"
                        self.status_msg = f"{self.p1.name}'s turn!"

    def draw_placement(self):
        self.draw_grid(self.p1.board, MARGIN, MARGIN + 50, "PLACE YOUR FLEET", hide_ships=False)
        msg1 = self.font.render("Press 'R' to rotate ship.", True, (255, 215, 0))
        self.screen.blit(msg1, (MARGIN, WINDOW_HEIGHT - 80))

        if self.ships_to_place:
            name, length = self.ships_to_place[0]
            msg2 = self.font.render(f"Placing: {name} (Length: {length})", True, TEXT_COLOR)
            self.screen.blit(msg2, (MARGIN, WINDOW_HEIGHT - 50))

            mouse_x, mouse_y = pygame.mouse.get_pos()
            board_x, board_y = MARGIN, MARGIN + 50
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE
                valid = self.p1.board.can_place(col, row, length, self.is_horizontal)
                color = GHOST_VALID if valid else GHOST_INVALID
                ghost_surface = pygame.Surface((CELL_SIZE * (length if self.is_horizontal else 1), 
                                                CELL_SIZE * (1 if self.is_horizontal else length)), pygame.SRCALPHA)
                ghost_surface.fill(color)
                self.screen.blit(ghost_surface, (board_x + col * CELL_SIZE, board_y + row * CELL_SIZE))

    # ─── PLAYING STATE ───────────────────────────────────
    def handle_playing_events(self, event):
        if self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
            self.state = "MENU" 
            return

        current_player = self.p1 if self.turn % 2 == 0 else self.p2
        defender = self.p2 if self.turn % 2 == 0 else self.p1

        if isinstance(current_player, HumanPlayer) and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            board_x, board_y = MARGIN, MARGIN + 50
            
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE

                if (col, row) not in current_player.tracking_grid.shots_received:
                    current_player.tracking_grid.shots_received.add((col, row))
                    result = defender.board.receive_shot(col, row)
                    current_player.record_shot_result(col, row, result)
                    self.process_shot_result(current_player, defender, result)

    def update_playing(self):
        if self.game_over: return
        current_player = self.p1 if self.turn % 2 == 0 else self.p2
        defender = self.p2 if self.turn % 2 == 0 else self.p1

        if not isinstance(current_player, HumanPlayer):
            self.ai_delay_timer += self.clock.get_time()
            if self.ai_delay_timer > 600: 
                col, row = current_player.choose_shot()
                result = defender.board.receive_shot(col, row)
                current_player.record_shot_result(col, row, result)
                self.process_shot_result(current_player, defender, result)
                self.ai_delay_timer = 0

    def process_shot_result(self, attacker, defender, result):
        if result == "hit": self.status_msg = f"{attacker.name} landed a HIT!"
        elif result.startswith("sunk"): self.status_msg = f"{attacker.name} SUNK the {result.split(':')[1]}!"
        else: self.status_msg = f"{attacker.name} missed."

        if defender.board.all_sunk():
            self.status_msg = f"GAME OVER! {attacker.name} WINS! (Click to return)"
            self.game_over = True
        else:
            self.turn += 1

    def draw_playing(self):
        left_x, right_x = MARGIN, MARGIN * 2 + BOARD_WIDTH
        y_offset = MARGIN + 50

        if self.mode == "PvAI":
            self.draw_grid(self.p1.tracking_grid, left_x, y_offset, "ENEMY WATERS", hide_ships=True)
            self.draw_grid(self.p1.board, right_x, y_offset, f"{self.p1.name.upper()}'S FLEET", hide_ships=False)
        else:
            self.draw_grid(self.p1.board, left_x, y_offset, f"{self.p1.name} (P1)", hide_ships=False)
            self.draw_grid(self.p2.board, right_x, y_offset, f"{self.p2.name} (P2)", hide_ships=False)

        msg_surf = self.font_large.render(self.status_msg, True, (255, 215, 0))
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 60)))

    # ─── CORE DRAWING METHOD ─────────────────────────────
    def draw_grid(self, board, x_offset, y_offset, title, hide_ships):
        title_surface = self.font.render(title, True, TEXT_COLOR)
        self.screen.blit(title_surface, (x_offset, y_offset - 30))

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell_state = board.grid[row][col]
                if hide_ships and cell_state == SHIP: cell_state = EMPTY

                rect = pygame.Rect(x_offset + (col * CELL_SIZE), y_offset + (row * CELL_SIZE), CELL_SIZE - 1, CELL_SIZE - 1)
                pygame.draw.rect(self.screen, COLOR_MAP.get(cell_state, COLOR_MAP[EMPTY]), rect)
                
                if cell_state in (HIT, SUNK):
                    pygame.draw.line(self.screen, (255,255,255), rect.topleft, rect.bottomright, 2)
                    pygame.draw.line(self.screen, (255,255,255), rect.bottomleft, rect.topright, 2)
                elif cell_state == MISS:
                    pygame.draw.circle(self.screen, (200,200,200), rect.center, 5)

    # ─── SIMULATION & STATS ──────────────────────────────
    def run_simulation(self, n):
        # Setup pure logical engine (no Pygame rendering for speed)
        self.stats = {"total": n, self.player1_name: 0, self.player2_name: 0}
        
        AI1 = HunterAI if self.ai1_type == "Hunter" else RandomAI
        AI2 = HunterAI if self.ai2_type == "Hunter" else RandomAI

        for _ in range(n):
            p1 = AI1(self.player1_name)
            p2 = AI2(self.player2_name)
            p1.board.place_all_random()
            p2.board.place_all_random()
            
            turn = 0
            while True:
                attacker = p1 if turn % 2 == 0 else p2
                defender = p2 if turn % 2 == 0 else p1
                
                col, row = attacker.choose_shot()
                result = defender.board.receive_shot(col, row)
                attacker.record_shot_result(col, row, result)
                
                if defender.board.all_sunk():
                    self.stats[attacker.name] += 1
                    break
                turn += 1
                
        self.state = "STATS"

    def draw_stats(self):
        title = self.font_large.render("SIMULATION STATISTICS", True, (100, 200, 255))
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 100)))
        
        n_text = self.font.render(f"Total Matches Simulated: {self.stats['total']}", True, TEXT_COLOR)
        
        # Calculate percentages
        p1_wins = self.stats[self.player1_name]
        p2_wins = self.stats[self.player2_name]
        p1_pct = (p1_wins / self.stats['total']) * 100
        p2_pct = (p2_wins / self.stats['total']) * 100

        p1_text = self.font_large.render(f"{self.player1_name} ({self.ai1_type}): {p1_wins} Wins ({p1_pct:.1f}%)", True, (50, 200, 80))
        p2_text = self.font_large.render(f"{self.player2_name} ({self.ai2_type}): {p2_wins} Wins ({p2_pct:.1f}%)", True, (220, 50, 50))
        
        self.screen.blit(n_text, n_text.get_rect(center=(WINDOW_WIDTH//2, 180)))
        self.screen.blit(p1_text, p1_text.get_rect(center=(WINDOW_WIDTH//2, 250)))
        self.screen.blit(p2_text, p2_text.get_rect(center=(WINDOW_WIDTH//2, 320)))
        
        self.btn_menu.draw(self.screen)

    # ─── MAIN LOOP ───────────────────────────────────────
    def run(self):
        while True:
            self.screen.fill(BG_COLOR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "MENU": self.handle_menu_events(event)
                elif self.state == "PLACEMENT": self.handle_placement_events(event)
                elif self.state == "PLAYING": self.handle_playing_events(event)
                elif self.state == "STATS":
                    if event.type == pygame.MOUSEBUTTONDOWN and self.btn_menu.is_clicked(event):
                        self.state = "MENU"

            if self.state == "MENU": self.draw_menu()
            elif self.state == "PLACEMENT": self.draw_placement()
            elif self.state == "PLAYING":
                self.update_playing()
                self.draw_playing()
            elif self.state == "STATS": self.draw_stats()

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    app = BattleshipGUI()
    app.run()
