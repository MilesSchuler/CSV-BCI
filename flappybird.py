 # Return key to restart, Esc key to quit
import mysql.connector

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

import pygame
import random

mydb = mysql.connector.connect(
    host = "mysql.2324.lakeside-cs.org",
    user = 'student2324',
    password = 'm545CS42324',
    database = '2324finalproject'
)

cursor = mydb.cursor()

username = 'Player 1'


# flappybird.py can't find training_constants on my laptop, using place, this is the placeholder (commented out):
# CHUNK_LENGTH = 2

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
FONT = pygame.font.Font('CSV_BCI/SundayMilk.ttf', 40)

TEXT_COLOR = (255, 245, 48)

# Constants
GRAVITY = 0.25
FLAP_STRENGTH = 5

global roundnum
roundnum = 0

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

def draw_text(text, x, y):
    img = FONT.render(text, True, TEXT_COLOR)
    WIN.blit(img, (x, y))

def add_username(new_username):
    global username 
    
    query = 'SELECT * FROM BCI_users WHERE name = %s'
    vals = (new_username,)

    cursor.execute(query, vals)

    potential_username = cursor.fetchall()

    if len(potential_username) > 0:
        username = potential_username[0]['name']
        print("We found it. ")
    else:
        query = 'INSERT INTO `BCI_users`(`name`, `high_score`) VALUES (%s,%s)'
        vals = (new_username, 0)
        cursor.execute(query, vals)
        
        mydb.commit()

        username = new_username

        print("We added it gang")

def main_menu():
    run = True

    username = ''

    input_rect = pygame.Rect(100, 200, 300, 35)
    enter_rect = pygame.Rect(305, 200, 35, 35)

    color_active = pygame.Color('lightskyblue3')
    color_passive = pygame.Color('black')

    color_input_rect = color_passive
    color_enter_rect = pygame.Color('grey')
    active = False 

    while run: 
        WIN.fill((89, 247, 239))
        msg = FONT.render("ENTER NICKNAME!", True, TEXT_COLOR)
        WIN.blit(msg, ((WIN.get_width() - msg.get_width())/2, 150))

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    active = True
                    color_input_rect = color_active
                elif enter_rect.collidepoint(event.pos) and len(username) > 0:
                    add_username(username)
                    start_game_loop()
                else:
                    active = False
                    color_input_rect = color_passive


            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(username) > 0:
                    add_username(username)
                    start_game_loop()
                elif event.key == pygame.K_BACKSPACE and active == True:
                    username = username[:-1]
                elif len(username) < 10 and active == True:
                    username += event.unicode

        pygame.draw.rect(WIN, color_input_rect, input_rect, 2, border_radius=10)
        pygame.draw.rect(WIN, color_enter_rect , enter_rect, border_radius = 10)
        text_surface = FONT.render(username, True, (0, 0, 0))
        WIN.blit(text_surface, (input_rect.x + 5, input_rect.y + 5)) 

        input_rect.w = max(150, text_surface.get_width() + 10)

        pygame.display.update()


# Main function
def start_game_loop():
    global roundnum
    roundnum += 1
    round = FONT.render(f"Round: {roundnum}", True, BLACK)
    WIN.blit(round, (WIDTH - round.get_width() - 10, 10))

    global bird
    bird = Bird()
    pipes = [Pipe(WIDTH + i * 250) for i in range(2)]
    clock = pygame.time.Clock()
    score = 0

    running = True
    while running:
        draw_text("YOU LOSE", 160, 250)

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

    

    while running == False:
        clock.tick(60)

        game_over_text = FONT.render("Game Over!", True, RED)
        restart_text = FONT.render("Press ENTER to restart or ESC to quit", True, BLACK)
        final_score_text = FONT.render(f"Score: {score}", True, BLACK)
        WIN.fill(WHITE)
        WIN.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - game_over_text.get_height()//2))
        WIN.blit(final_score_text, (10,10))
        WIN.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + game_over_text.get_height()))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_RETURN:
                    running = True
                    start_game_loop()

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


# streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread)
# streaming_thread.start()
main_menu()

