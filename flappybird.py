 # Return key to restart, Esc key to quit
import mysql.connector

from LiveCollectionData.muse_utility import stream, list_muses
import asyncio
import time
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

username = ''

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

# sky colors
morning_color = (179, 246, 255)  # light blue
night_color = (25, 25, 112)  # dark blue

# Fonts
FONT = pygame.font.Font('CSV_BCI/Fonts/SundayMilk.ttf', 30)

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

# Coin class
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.Rect(self.x, self.y, 20, 20)

    def move(self):
        self.x -= 2
        self.image.x = self.x

    def draw(self):
        pygame.draw.rect(WIN, RED, self.image)

# generating coins that don't overlap with pipes
def generate_coins(pipes):
    while True:
        coin_x = random.randint(WIDTH, WIDTH + 800)
        coin_y = random.randint(100, HEIGHT - 100)
        new_coin = pygame.Rect(coin_x, coin_y, 20, 20)
        overlap = False
        for pipe in pipes:
            if new_coin.colliderect(pipe.top_pipe) or new_coin.colliderect(pipe.bottom_pipe):
                overlap = True
                break
        if not overlap:
            return Coin(coin_x, coin_y)
        

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
        # assuming 'name' is the first column in the database
        username = potential_username[0][0]
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

    input_rect = pygame.Rect(120, 200, 300, 35)
    enter_rect = pygame.Rect(305, 200, 35, 35)

    color_active = pygame.Color('lightskyblue3')
    color_passive = pygame.Color('black')

    color_input_rect = color_passive
    color_enter_rect = pygame.Color('grey')
    active = False 

    while run: 
        WIN.fill(morning_color)
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


# Finding color based on "time"
def sky_color():
    elapsed_time = pygame.time.get_ticks()
    total_time = 120000  # 2 min for a complete color cycle
    t = (elapsed_time % (total_time / 2)) / total_time  # Fraction of the way through the half cycle

    if (elapsed_time % total_time) < (total_time / 2): # Less than halfway through cycle
        # Go from day to night
        return (int(morning_color[0] + (night_color[0] - morning_color[0]) * t),
                int(morning_color[1] + (night_color[1] - morning_color[1]) * t),
                int(morning_color[2] + (night_color[2] - morning_color[2]) * t)) 
    else: # Halfway or more through cycle
        # Go from night to day
        return (int(night_color[0] + (morning_color[0] - night_color[0]) * t),
                int(night_color[1] + (morning_color[1] - night_color[1]) * t),
                int(night_color[2] + (morning_color[2] - night_color[2]) * t)) 


# Main function
def start_game_loop():
    global morning_color
    global night_color

    global roundnum
    roundnum += 1
    start_time = pygame.time.get_ticks()

    global bird
    bird = Bird()
    pipes = [Pipe(WIDTH + i * 250) for i in range(2)]
    coins = [generate_coins(pipes) for _ in range(5)]
    clock = pygame.time.Clock()
    score = 0

    running = True
    while running:
        clock.tick(60)

        color = sky_color()
        WIN.fill(color)

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

        for coin in coins:
            coin.move()
            if coin.x < 0:
                coins.remove(coin)
                coins.append(Coin(random.randint(WIDTH, WIDTH + 800), random.randint(100, HEIGHT - 100)))

            if bird.image.colliderect(coin.image):
                coins.remove(coin)
                coins.append(Coin(random.randint(WIDTH, WIDTH + 800), random.randint(100, HEIGHT - 100)))
                score += 10

        if bird.y > HEIGHT or bird.y < 0:
            running = False

        bird.draw()
        for pipe in pipes:
            pipe.draw()
        for coin in coins:
            coin.draw()
        
        score_text = FONT.render(f"Score: {score}", True, BLACK)
        WIN.blit(score_text, (10, 10))

        round = FONT.render(f"Round: {roundnum}", True, BLACK)
        WIN.blit(round, (WIN.get_width() - round.get_width() - 10, 10))

        pygame.display.update()

    
    # True if they broke old high score, false if they did not. 
    new_high = update_high_score(score) 

    while running == False:
        clock.tick(60)

        game_over_text = FONT.render("Game Over!", True, RED)
        restart_text1 = FONT.render("Press ENTER to restart", True, BLACK)
        restart_text2 = FONT.render("Press ESC to quit", True, BLACK)
        final_score_text = FONT.render(f"Score: {score}", True, BLACK)
        current_round = FONT.render(f"Round: {roundnum}", True, BLACK)
        WIN.fill(WHITE)
        WIN.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - game_over_text.get_height()//2))
        WIN.blit(final_score_text, (10,10))
        WIN.blit(current_round, (WIN.get_width() - round.get_width() - 10, 10))
        WIN.blit(restart_text1, (WIDTH//2 - restart_text1.get_width()//2, HEIGHT//2 + game_over_text.get_height()))
        WIN.blit(restart_text2, (WIDTH//2 - restart_text2.get_width()//2, HEIGHT//2 + restart_text1.get_height()
                                 + game_over_text.get_height()))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
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


# Takes in the score player just had and updates database if it's a new high score
# Returns true if they had a new high score and false if they didn't 

def update_high_score(score):
    query = "SELECT * FROM BCI_users WHERE name = %s AND high_score < %s"
    vals = (username, score)

    cursor.execute(query, vals)

    query_return = cursor.fetchall()

    if len(query_return) > 0:
        query = "UPDATE `BCI_users` SET `high_score`= %s WHERE name = %s"
        print(username)
        vals = (score,username)

        cursor.execute(query, vals)
        mydb.commit()
        
        return True
    
    return False 

# streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread)
# streaming_thread.start()
main_menu()

