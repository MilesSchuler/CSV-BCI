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
previous_xs = []

loaded_model = tf.keras.models.load_model('data_test.keras')

def start_stream_thread(address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))

def chunk_generator(arr, length, overlap):
    for i in range(0, len(arr), length - overlap):
        yield arr[i:i + length]

def analyze_muse(data, timestamp):
    global previous_xs
    global bird
    # add previous_xs to start of checkable_x
    checkable_xs = previous_xs
    
    # add data to checkable_x
    for row in data:
        input = [
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4])
        ]

        checkable_xs.append(input)

    # set previous_xs to leftovers from checkable_x
    gen = chunk_generator(checkable_xs, CHUNK_LENGTH, 1)
    chunks = [chunk for chunk in gen]
    previous_xs = chunks.pop()

    if len(chunks) > 0:
        for chunk in chunks:
            input = np.array(chunk).flatten()
            input = input.reshape(1, -1)  # Add a batch dimension
            if input.shape == (1, CHUNK_LENGTH * 4):
                prediction = loaded_model.predict(input, verbose=0)
                prediction = prediction[0]
                # [0, 1] for blink
                if prediction[1] > BLINK_THRESHOLD:
                    print("blink")
                    
                    bird.flap()

            else:
                pass
            #print(input.shape)


muse_address = list_muses()[0]['address']
streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread, args=(muse_address,))
streaming_thread.start()

sleep(10.)

streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
if len(streams) == 0:
    raise(RuntimeError("Can't find EEG stream."))
print("Start acquiring data.")

streamer = Streamer(streams[0], analyze_muse)
streamer.start(1/60)