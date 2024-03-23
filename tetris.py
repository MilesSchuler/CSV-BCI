import pygame
import random
import csv
from datetime import datetime
import time

# Define constants
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = SCREEN_WIDTH // GRID_WIDTH

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)

# Define tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1],
     [0, 1, 0]],  # T
    [[0, 1, 1],
     [1, 1, 0]],  # S
    [[1, 1, 0],
     [0, 1, 1]],  # Z
    [[1, 1, 1],
     [0, 0, 1]],  # J
    [[1, 1, 1],
     [1, 0, 0]],  # L
    [[1, 1],
     [1, 1]]  # O
]

SHAPES_COLORS = [
    CYAN,   # I
    MAGENTA,  # T
    GREEN,   # S
    RED,     # Z
    BLUE,    # J
    ORANGE,  # L
    YELLOW   # O
]

class Tetromino:
    def __init__(self, shape, color):
        self.shape = shape
        self.color = color
        self.x = GRID_WIDTH // 2 - len(shape[0]) // 2
        self.y = 0

    def draw(self, screen):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, self.color, (self.x * BLOCK_SIZE + x * BLOCK_SIZE,
                                                           self.y * BLOCK_SIZE + y * BLOCK_SIZE,
                                                           BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, BLACK, (self.x * BLOCK_SIZE + x * BLOCK_SIZE,
                                                     self.y * BLOCK_SIZE + y * BLOCK_SIZE,
                                                     BLOCK_SIZE, BLOCK_SIZE), 1)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.grid = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.logged_key_presses = []
    
    
    def log_key_press(self, key):
        timestamp = time.time()
        self.logged_key_presses.append((timestamp, key))
    
    def log_key_presses(self):
        filename = "Tetris " + str(datetime.now()).replace(':', '.') + ".csv"
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['timestamp', 'key'])
            for timestamp, key in self.logged_key_presses:
                csvwriter.writerow([timestamp, key])
        
        print('Done - wrote file: ' + filename + '.')

    def new_piece(self):
        shape = random.choice(SHAPES)
        color = random.choice(SHAPES_COLORS)
        return Tetromino(shape, color)

    def draw_grid(self):
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, cell, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(self.screen, BLACK, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw(self):
        self.screen.fill(WHITE)
        self.draw_grid()
        self.current_piece.draw(self.screen)
        pygame.display.update()

    def run(self):
        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move_piece(-1, 0)
                        self.log_key_press("left")
                    elif event.key == pygame.K_RIGHT:
                        self.move_piece(1, 0)
                        self.log_key_press("right")
                    elif event.key == pygame.K_DOWN:
                        self.move_piece(0, 1)
                        self.log_key_press("down")
                    elif event.key == pygame.K_UP:
                        self.current_piece.rotate()
                        self.log_key_press("up")

            self.move_piece(0, 1)
            self.draw()
            self.clock.tick(5)
        self.log_key_presses()

    def move_piece(self, dx, dy):
        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        if self.valid_position(new_x, new_y, self.current_piece.shape):
            self.current_piece.move(dx, dy)
        else:
            if dy == 1:  # Check if piece reached the bottom
                self.lock_piece()

    def valid_position(self, x, y, shape):
        for row_index, row in enumerate(shape):
            for cell_index, cell in enumerate(row):
                if cell:
                    # Check if the destination cell is within the grid boundaries
                    if not 0 <= x + cell_index < GRID_WIDTH or not 0 <= y + row_index < GRID_HEIGHT:
                        return False
                    # Check if the destination cell is empty
                    if self.grid[y + row_index][x + cell_index]:
                        return False
        return True

    def clear_lines(self, lines):
        for line in lines:
            del self.grid[line]
            self.grid.insert(0, [None] * GRID_WIDTH)


    def lock_piece(self):
        for row_index, row in enumerate(self.current_piece.shape):
            for cell_index, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece.y + row_index][self.current_piece.x + cell_index] = self.current_piece.color
        
        # Check for completed lines and clear them
        lines_to_clear = []
        for i, row in enumerate(self.grid):
            if all(row):
                lines_to_clear.append(i)
        if lines_to_clear:
            self.clear_lines(lines_to_clear)

        # Check if any cells in the top row are occupied
        if any(self.grid[0]):
            self.game_over = True
        else:
            self.current_piece = self.new_piece()

if __name__ == "__main__":
    pygame.init()
    game = TetrisGame()
    game.run()
    pygame.quit()

