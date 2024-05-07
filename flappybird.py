from LiveCollectionData.muse_utility import stream, list_muses
import asyncio
from time import sleep
from pylsl import resolve_byprop
from threading import Thread
from LiveCollectionData.streamer import Streamer
from muselsl.constants import LSL_SCAN_TIMEOUT
import sys
import numpy as np
import tensorflow as tf
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP, BLINK_THRESHOLD
import pygame
import random

pygame.init()

# Set up display
WIDTH, HEIGHT = 400, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Fonts
FONT = pygame.font.SysFont(None, 40)

# Constants
GRAVITY = 0.25
FLAP_STRENGTH = 5

global bird
# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = HEIGHT // 2
        self.velocity = 0
        self.lift = -FLAP_STRENGTH
        self.image = pygame.Rect(self.x, self.y, 30, 30)

    def flap(self):
        self.velocity = self.lift

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.image.y = self.y

    def draw(self):
        pygame.draw.rect(WIN, BLACK, self.image)

# Pipe class
class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(150, 400)
        self.top_pipe = pygame.Rect(self.x, 0, 50, self.height)
        self.bottom_pipe = pygame.Rect(self.x, self.height + 200, 50, HEIGHT - self.height - 200)
        self.passed = False

    def move(self):
        self.x -= 2
        self.top_pipe.x = self.x
        self.bottom_pipe.x = self.x

    def draw(self):
        pygame.draw.rect(WIN, GREEN, self.top_pipe)
        pygame.draw.rect(WIN, GREEN, self.bottom_pipe)

# Main function
def start_game_loop():
    global bird
    bird = Bird()
    pipes = [Pipe(WIDTH + i * 300) for i in range(2)]
    clock = pygame.time.Clock()
    score = 0

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()

        bird.update()

        for pipe in pipes:
            pipe.move()
            if pipe.top_pipe.right < 0:
                pipes.remove(pipe)
                pipes.append(Pipe(WIDTH))

            if bird.image.colliderect(pipe.top_pipe) or bird.image.colliderect(pipe.bottom_pipe):
                running = False
            elif not pipe.passed and pipe.top_pipe.right < bird.x:
                pipe.passed = True
                score += 1

        if bird.y > HEIGHT or bird.y < 0:
            running = False

        WIN.fill(WHITE)
        bird.draw()
        for pipe in pipes:
            pipe.draw()
        score_text = FONT.render(f"Score: {score}", True, BLACK)
        WIN.blit(score_text, (10, 10))
        pygame.display.update()

    pygame.quit()

PREVIOUS = 25
previous = []

def start_stream_thread():
    streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
    if len(streams) == 0:
        raise(RuntimeError("Can't find EEG stream."))
    print("Start acquiring data.")

    streamer = Streamer(streams[0], analyze_muse)
    streamer.start(1/60)

def chunk_generator(arr, length, overlap):
    for i in range(0, len(arr), length - overlap):
        yield arr[i:i + length]

def analyze_muse(data, timestamp):
    global previous
    global bird

    tp9 = 0

    for row in data:
        tp9 += row[0]
    
    tp9 = tp9/12

    if len(previous) < 5:
        previous.append(tp9)
    else:
        previous.pop(0)
        previous.append(tp9)
    
    if previous[-1] < (previous[0] - 120):
        print('blink')
        bird.flap()


streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread)
streaming_thread.start()
start_game_loop()
