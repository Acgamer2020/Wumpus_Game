import random
from collections import deque

GRID_SIZE = 4


class Cell:
    def __init__(self):
        self.pit = False
        self.wumpus = False
        self.gold = False
        self.breeze = False
        self.stench = False


class WumpusGame:
    def __init__(self):
        self.grid = [[Cell() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.start = (0, 0)
        self.agent = self.start
        self.has_gold = False
        self.game_over = False
        self.win = False
        self.visited = {self.start}

        self.score = 0
        self.arrow_used = False

        self.generate_world()

    def in_bounds(self, r, c):
        return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

    def neighbors(self, r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                yield nr, nc

    def generate_world(self):
        while True:
            self.grid = [[Cell() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

            all_cells = [
                (r, c)
                for r in range(GRID_SIZE)
                for c in range(GRID_SIZE)
                if (r, c) != self.start
            ]

            wumpus_pos = random.choice(all_cells)
            remaining = [pos for pos in all_cells if pos != wumpus_pos]
            gold_pos = random.choice(remaining)
            remaining = [pos for pos in remaining if pos != gold_pos]

            pit_count = random.randint(2, 4)
            pits = set(random.sample(remaining, pit_count))

            self.grid[wumpus_pos[0]][wumpus_pos[1]].wumpus = True
            self.grid[gold_pos[0]][gold_pos[1]].gold = True
            for r, c in pits:
                self.grid[r][c].pit = True

            self.add_clues()

            if self.path_exists(self.start, gold_pos):
                break

    def add_clues(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid[r][c]
                if cell.pit:
                    for nr, nc in self.neighbors(r, c):
                        self.grid[nr][nc].breeze = True
                if cell.wumpus:
                    for nr, nc in self.neighbors(r, c):
                        self.grid[nr][nc].stench = True

    def path_exists(self, start, goal):
        queue = deque([start])
        seen = {start}

        while queue:
            r, c = queue.popleft()
            if (r, c) == goal:
                return True

            for nr, nc in self.neighbors(r, c):
                if (nr, nc) in seen:
                    continue
                if self.grid[nr][nc].pit or self.grid[nr][nc].wumpus:
                    continue
                seen.add((nr, nc))
                queue.append((nr, nc))

        return False

    def current_cell(self):
        r, c = self.agent
        return self.grid[r][c]

    def get_percepts(self):
        cell = self.current_cell()
        percepts = []
        if cell.breeze:
            percepts.append("Breeze")
        if cell.stench:
            percepts.append("Stench")
        if cell.gold and not self.has_gold:
            percepts.append("Glitter")
        if not percepts:
            percepts.append("Nothing unusual")
        return percepts

    def display_board(self, reveal=False):
        print("\n   0   1   2   3")
        print(" +---+---+---+---+")
        for r in range(GRID_SIZE):
            row = f"{r}|"
            for c in range(GRID_SIZE):
                if (r, c) == self.agent:
                    content = "A"
                else:
                    cell = self.grid[r][c]
                    if reveal:
                        if cell.pit:
                            content = "P"
                        elif cell.wumpus:
                            content = "W"
                        elif cell.gold:
                            content = "G"
                        else:
                            content = " "
                    else:
                        if (r, c) in self.visited:
                            content = "."
                        else:
                            content = "?"
                row += f" {content} |"
            print(row)
            print(" +---+---+---+---+")
        print("Legend: A=Agent, ?=Unknown, .=Visited, P=Pit, W=Wumpus, G=Gold")

    def print_state(self, title):
        print(f"\n{title}")
        self.display_board(reveal=self.game_over or self.win)
        print(f"Position: {self.agent}")
        print("Percepts: " + ", ".join(self.get_percepts()))
        print(f"Gold collected: {'Yes' if self.has_gold else 'No'}")
        print(f"Score: {self.score}")

    def apply_action_penalty(self):
        self.score -= 1

    def move_agent(self, direction):
        self.apply_action_penalty()

        r, c = self.agent
        direction = direction.lower()

        moves = {
            "w": (-1, 0),
            "a": (0, -1),
            "s": (1, 0),
            "d": (0, 1),
        }

        if direction not in moves:
            return "Invalid move. Use W, A, S, D, G, F, or Q."

        dr, dc = moves[direction]
        nr, nc = r + dr, c + dc

        if not self.in_bounds(nr, nc):
            return "You bumped into a wall."

        self.agent = (nr, nc)
        self.visited.add(self.agent)

        cell = self.current_cell()

        if cell.pit:
            self.game_over = True
            self.score -= 1000
            return "You fell into a pit. Game over."

        if cell.wumpus:
            self.game_over = True
            self.score -= 1000
            return "The Wumpus got you. Game over."

        return f"Moved to {self.agent}."

    def grab_gold(self):
        self.apply_action_penalty()

        cell = self.current_cell()
        if cell.gold and not self.has_gold:
            self.has_gold = True
            cell.gold = False
            return "You picked up the gold."
        return "There is no gold here."

    def fire_arrow(self, direction):
        if self.arrow_used:
            return "You already used your arrow."
        
        self.apply_action_penalty()
        self.score -= 10
        self.arrow_used = True

        direction = direction.lower()
        moves = {
            "w": (-1, 0),
            "a": (0, -1),
            "s": (1, 0),
            "d": (0, 1),
        }

        if direction not in moves:
            return "Invalid arrow direction."

        dr, dc = moves[direction]
        r, c = self.agent

        nr, nc = r + dr, c + dc
        while self.in_bounds(nr, nc):
            if self.grid[nr][nc].wumpus:
                self.grid[nr][nc].wumpus = False
                return "Your arrow hit the Wumpus. You hear a scream!"
            nr += dr
            nc += dc

        return "Your arrow missed."

    def check_win(self):
        if self.has_gold and self.agent == self.start:
            self.win = True
            self.score += 1000
            return True
        return False

    def play(self):
        print("=== WUMPUS GAME ===")
        print("Controls: W=up, A=left, S=down, D=right, G=grab gold, F=fire arrow, Q=quit")
        print("Goal: get the gold and return to the start (0, 0) alive.")
        print("Scoring: +1000 win, -1000 death, -1 per action, -10 for arrow use.\n")

        while not self.game_over and not self.win:
            self.print_state("Before move")
            command = input("Enter move: ").strip().lower()

            if not command:
                continue

            if command == "q":
                print("\nYou quit the game.")
                return

            if command == "g":
                result = self.grab_gold()

            elif command == "f":
                arrow_dir = input("Fire arrow in which direction? (W/A/S/D): ").strip().lower()
                result = self.fire_arrow(arrow_dir)

            else:
                result = self.move_agent(command)

            print(f"\nMove: {command.upper()}")
            print(result)

            if not self.game_over:
                self.check_win()

            self.print_state("After move")

        if self.win:
            print("\nYou returned to the start with the gold. You win!")
        elif self.game_over:
            print("\nYou lost the game.")
        else:
            print("\nGame ended.")

        print(f"Final Score: {self.score}")
        print("\nFinal world map:")
        self.display_board(reveal=True)


if __name__ == "__main__":
    game = WumpusGame()
    game.play()