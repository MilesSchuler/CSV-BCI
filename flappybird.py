 # Return key to restart, Esc key to quit
import mysql.connector

from LiveCollectionData.muse_utility import stream, list_muses
from LiveCollectionData.streamer import Streamer
from muselsl.constants import LSL_SCAN_TIMEOUT
import sys
import numpy as np

from scipy.signal import lfilter, lfilter_zi, firwin
from usingmuselsl.training_constants import CHUNK_LENGTH, BLINK_THRESHOLD
from time import sleep
from pylsl import StreamInlet, resolve_byprop
from threading import Thread
from time import gmtime, strftime, time

import tensorflow as tf

import pygame
import random

# Setting to true allows bird to ignore all pipes for testing purposes
testing = False

# Set to false if needing to test non-blink gameplay
USE_BLINK_DETECTION = True
MAX_SAMPLES = 24
DEJITTER = True
ai_blink_timestamps = []
blink_calls = []

# Ensuring you can't start the game before the muse stream is connected
global connected
connected = False
if not USE_BLINK_DETECTION:
    connected = True

# Database connection setup
mydb = mysql.connector.connect(
    host = "mysql.2324.lakeside-cs.org",
    user = 'student2324',
    password = 'm545CS42324',
    database = '2324finalproject'
)

cursor = mydb.cursor()

username = ''

# Initialize pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 400, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")

# color palettes
global MORNING_PALETTE
MORNING_PALETTE = [(222, 229, 255), # sky
                   (128, 67, 41), # pipes
                   (110, 41, 128), # bird and text color 2
                   (41, 59, 128), # text
                   (218, 221, 109) # coins
                   ]
global NIGHT_PALETTE
NIGHT_PALETTE = [(41, 59, 128), # sky
                 (255, 232, 222), # pipes
                 (248, 222, 255), # bird and text color 2
                 (222, 229, 255), # text
                 (254, 255, 219) # coins
                 ]

# Fonts
FONT = pygame.font.Font('Fonts/SundayMilk.ttf', 30)
BIG_FONT = pygame.font.Font('Fonts/SundayMilk.ttf', 50)

# colors again (for ease of use)
global TEXT_COLOR
TEXT_COLOR = MORNING_PALETTE[3]
global TEXT_COLOR2
TEXT_COLOR2 = MORNING_PALETTE[2]

# Bird constants
GRAVITY = 0.25
FLAP_STRENGTH = 5

# Keeping track of rounds
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
        self.draw()

    def draw(self):
        pygame.draw.rect(WIN, palette_color(2), self.image)

# Coin class
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.Rect(self.x, self.y, 20, 20)

    def move(self):
        self.x -= 2
        self.image.x = self.x
        self.draw()

    def draw(self):
        pygame.draw.rect(WIN, palette_color(4), self.image)

# Generating coins
def generate_coins(pipes):
    while True:
        coin_x = random.randint(WIDTH, WIDTH + 800)
        coin_y = random.randint(100, HEIGHT - 100)
        new_coin = pygame.Rect(coin_x, coin_y, 20, 20)
        overlap = False
        for pipe in pipes:
            # Buffer rectangles for nicer coin placement
            buffer_top_pipe = pipe.top_pipe.inflate(10, 10)
            buffer_bottom_pipe = pipe.bottom_pipe.inflate(10, 10) 

            if (new_coin.colliderect(buffer_top_pipe) or new_coin.colliderect(buffer_bottom_pipe)):
                overlap = True
                break
        if not overlap:
            return Coin(coin_x, coin_y)
        

# Pipe class
class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(50, 300)
        self.top_pipe = pygame.Rect(self.x, 0, 50, self.height)
        self.bottom_pipe = pygame.Rect(self.x, self.height + 250, 50, HEIGHT - self.height - 250)
        self.passed = False

    def move(self):
        self.x -= 2
        self.top_pipe.x = self.x
        self.bottom_pipe.x = self.x
        self.draw()

    def draw(self):
        pygame.draw.rect(WIN, palette_color(1), self.top_pipe)
        pygame.draw.rect(WIN, palette_color(1), self.bottom_pipe)

def draw_text(text, x, y, color):
    img = FONT.render(text, True, color)
    WIN.blit(img, (x, y))

# adding new users
def add_username(new_username):
    global username 
    
    # checking to see if a new username needs to be added
    query = 'SELECT * FROM BCI_users WHERE name = %s'
    vals = (new_username,)

    cursor.execute(query, vals)

    potential_username = cursor.fetchall()

    if len(potential_username) > 0:
        # assuming 'name' is the first column in the database
        username = potential_username[0][0]
    else:
        query = 'INSERT INTO `BCI_users`(`name`, `high_score`) VALUES (%s,%s)'
        vals = (new_username, 0)
        cursor.execute(query, vals)
        
        mydb.commit()

        username = new_username

# Generates the leaderboard found through the home page
def show_leaderboard():
    global rankings

    # For pagination
    ITEMS_PER_PAGE = 5
    current_page = 0

    rankings = leaderboard()
    rankings.sort(key=lambda x: x[1], reverse=True) # Sorts users from highest to lowest score

    run = True

    def draw_leaderboard():
        start_index = current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

        WIN.fill(MORNING_PALETTE[0])

        # Back button
        back_rect = pygame.Rect(10, 10, 160, 35)
        color_back_rect = MORNING_PALETTE[3]
        pygame.draw.rect(WIN, color_back_rect, back_rect, border_radius = 10)
        back_text = FONT.render("Go back", True, MORNING_PALETTE[0])
        WIN.blit(back_text, back_text.get_rect(center=back_rect.center))

        msg = FONT.render(f"LEADERBOARD ({start_index + 1} - {min(end_index, len(rankings))})", True, TEXT_COLOR)
        WIN.blit(msg, ((WIN.get_width() - msg.get_width()) / 2, 100))

        # Displays rankings
        for i, (name, score) in enumerate(rankings[start_index:end_index]):
            rank_text = FONT.render(f"{start_index + i + 1}. {name}: {score}", True, TEXT_COLOR)
            WIN.blit(rank_text, (50, 200 + i * 30))

        # Variables for pagination
        prev_rect = next_rect = prev_text = next_text = None

        if current_page > 0: # If not on first page, show the prev button
            prev_rect = pygame.Rect(10, HEIGHT - 50, 70, 35)
            pygame.draw.rect(WIN, MORNING_PALETTE[3], prev_rect, border_radius = 10)
            prev_text = FONT.render("Prev", True, MORNING_PALETTE[0])
            WIN.blit(prev_text, prev_text.get_rect(center=prev_rect.center))

        if end_index < len(rankings): # If not on last page, show the next button
            next_rect = pygame.Rect(WIDTH - 80, HEIGHT - 50, 70, 35)
            pygame.draw.rect(WIN, MORNING_PALETTE[3], next_rect, border_radius = 10)
            next_text = FONT.render("Next", True, MORNING_PALETTE[0])
            WIN.blit(next_text, next_text.get_rect(center=next_rect.center))
        
        pygame.display.update()
        
        return back_rect, prev_rect, next_rect



    while run:
        back_rect, prev_rect, next_rect = draw_leaderboard()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos): # Return to main menu
                    run = False
                
                elif prev_rect and prev_rect.collidepoint(event.pos): # Previous page
                    current_page -= 1
                    break
                elif next_rect and next_rect.collidepoint(event.pos): # Next page
                    current_page += 1
                    break
    
    main_menu()


def main_menu():
    run = True

    username = ''

    # Blinking cursor
    cursor_visible = True
    CURSOR_CYCLE = 700
    cursor_timer = 0

    # Username input rectangle
    input_rect = pygame.Rect(120, 250, 300, 35)

    # Play button
    button_text = FONT.render('PLAY',True, MORNING_PALETTE[0])
    play_button = pygame.Rect(300, 250, button_text.get_width() + 10, 35)

    leaderboard_rect = pygame.Rect(10, 10, 240, 35)

    color_active = MORNING_PALETTE[2]
    color_passive = MORNING_PALETTE[3]

    color_input_rect = color_passive
    color_enter_rect = MORNING_PALETTE[3]
    color_leaderboard_rect = MORNING_PALETTE[3]
    active = False 

    while run: 
        WIN.fill(MORNING_PALETTE[0])
        
        header = BIG_FONT.render("FLAPPYBIRD", True, TEXT_COLOR)
        header_rect = header.get_rect(center = (WIN.get_width()/2, 120))
        WIN.blit(header, header_rect)

        ## not using get_rect here because the spacing makes more sense
        ## get_rect creates too much spacing between "ENTER NICKNAME" and the text box 
        msg = FONT.render("ENTER NICKNAME!", True, TEXT_COLOR)
        WIN.blit(msg, ((WIN.get_width() - msg.get_width())/2, 200))

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    active = True
                    color_input_rect = color_active # "select" the input rectangle (visual feedback)
                elif play_button.collidepoint(event.pos) and len(username) > 0:
                    if connected:
                        add_username(username)
                        start_game_loop()
                elif leaderboard_rect.collidepoint(event.pos):
                    show_leaderboard()
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

        cursor_timer = pygame.time.get_ticks() % CURSOR_CYCLE
        # Update cursor visibility
        if cursor_timer < (CURSOR_CYCLE) / 2:
            cursor_visible = True
        else:
            cursor_visible = False

        pygame.draw.rect(WIN, color_input_rect, input_rect, 2, border_radius=10)
        pygame.draw.rect(WIN, color_enter_rect, play_button, border_radius = 10)

        pygame.draw.rect(WIN, color_leaderboard_rect, leaderboard_rect, border_radius = 10)
        text_surface = FONT.render(username, True, TEXT_COLOR)
        WIN.blit(text_surface, (input_rect.x + 5, input_rect.y + 5)) 

        WIN.blit(button_text, (play_button.x + 5, play_button.y + 5))

        leaderboard_text = FONT.render("Show Leaderboard", True, MORNING_PALETTE[0])
        WIN.blit(leaderboard_text, leaderboard_text.get_rect(center=leaderboard_rect.center))


        ## write instructions 
        instruct_head = FONT.render("HOW TO PLAY:", True, TEXT_COLOR)
        instruct_1 = FONT.render("1. Blink to jump", True, TEXT_COLOR)
        instruct_2 = FONT.render("2. Collect coins", True, TEXT_COLOR)
        instruct_3 = FONT.render("3. Avoid columns!", True, TEXT_COLOR)

        header_y = 350

        WIN.blit(instruct_head, instruct_head.get_rect(center = (WIN.get_width()/2, header_y)))
        WIN.blit(instruct_1, ((WIN.get_width()/2) - 100, header_y + 50))
        WIN.blit(instruct_2, ((WIN.get_width()/2) - 100, header_y + 100))
        WIN.blit(instruct_3, ((WIN.get_width()/2) - 100, header_y + 150))

        # Draw cursor if visible and input box is active
        if cursor_visible and active:
            cursor_x = input_rect.x + text_surface.get_width() + 5
            cursor_rect = pygame.Rect(cursor_x, input_rect.y + 5, 2, text_surface.get_height())
            pygame.draw.rect(WIN, color_active, cursor_rect)

        input_rect.w = max(150, text_surface.get_width() + 10)

        pygame.display.update()

# Finding color based on "time"
def palette_color(num):
    elapsed_time = pygame.time.get_ticks()
    total_time = 120000  # 2 min for a complete color cycle
    cycle_time = elapsed_time % total_time
    t = cycle_time / total_time  # Fraction of the way through the cycle

    if cycle_time < (total_time / 4): # First 4th of the cycle
        # Daytime
        return MORNING_PALETTE[num]
    elif cycle_time < (total_time / 2):
        # Transition to night
        return (interpolate_color(MORNING_PALETTE[num], NIGHT_PALETTE[num], (t - 0.25) * 4))
    elif cycle_time < (3 * (total_time) / 4):
        # Night
        return NIGHT_PALETTE[num]
    else:
        # Transition to day
        return (interpolate_color(NIGHT_PALETTE[num], MORNING_PALETTE[num], (t - 0.75) * 4))

        
# Interpolating from color 1 to 2
def interpolate_color(color1, color2, t):
    # t is in [0,1]
    return (int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t))

# Main function
def start_game_loop():
    global testing

    global roundnum
    roundnum += 1

    # Setup
    global bird
    bird = Bird()
    pipes = [Pipe(WIDTH + i * 250) for i in range(2)]
    coins = [generate_coins(pipes) for _ in range(5)]
    clock = pygame.time.Clock()
    score = 0

    if USE_BLINK_DETECTION:
        bird.lift = -3.5

    running = True
    while running:
        clock.tick(60)

        color = palette_color(0) # sky color changes based on in-game time
        WIN.fill(color)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not USE_BLINK_DETECTION:
                        bird.flap()

        # DO BLINK DETECTION HERE
        if USE_BLINK_DETECTION:
            # make sure its not empty
            if blink_calls:
                if blink_calls[-1] == "blink":
                    bird.flap()

        bird.update()

        # Pipe generation, movement, interactions
        for pipe in pipes:
            pipe.move()
            if pipe.top_pipe.right < 0:
                pipes.remove(pipe)
                pipes.append(Pipe(WIDTH))

            if (bird.image.colliderect(pipe.top_pipe) or bird.image.colliderect(pipe.bottom_pipe)) and testing == False:
                running = False
            elif not pipe.passed and pipe.top_pipe.right < bird.x:
                pipe.passed = True
                score += 1

        # Coin generation, movement, interactions
        for coin in coins:
            coin.move()
            if coin.x < 0:
                coins.remove(coin)
                coins.append(Coin(random.randint(WIDTH, WIDTH + 800), random.randint(100, HEIGHT - 100)))

            if bird.image.colliderect(coin.image):
                coins.remove(coin)
                coins.append(Coin(random.randint(WIDTH, WIDTH + 800), random.randint(100, HEIGHT - 100)))
                score += 10

        if bird.y > HEIGHT or bird.y < 0: # If you crash into the top/bottom
            running = False

        bird.draw()
        for pipe in pipes:
            pipe.draw()
        for coin in coins:
            coin.draw()
        
        score_text = FONT.render(f"Score: {score}", True, palette_color(3))
        WIN.blit(score_text, (10, 10))

        round = FONT.render(f"Round: {roundnum}", True, palette_color(3))
        WIN.blit(round, (WIN.get_width() - round.get_width() - 10, 10))

        pygame.display.update()

    
    # True if they broke old high score, false if they did not. 
    new_high = update_high_score(score) 

    while running == False:
        clock.tick(60)

        congrats_text = ''
        if new_high:
            congrats_text = FONT.render(f"NEW HIGH SCORE: {score}", True, TEXT_COLOR)
        
        game_over_text = BIG_FONT.render("Game Over!", True, TEXT_COLOR2)
        restart_text1 = FONT.render("Press ENTER to restart", True, TEXT_COLOR)
        restart_text2 = FONT.render("Press ESC to quit", True, TEXT_COLOR)
        final_score_text = FONT.render(f"Score: {score}", True, TEXT_COLOR)
        current_round = FONT.render(f"Round: {roundnum}", True, TEXT_COLOR)
        WIN.fill(MORNING_PALETTE[0])
        if new_high:
            WIN.blit(congrats_text, (WIDTH//2 - congrats_text.get_width()//2, HEIGHT//2 - congrats_text.get_height()//2))
        
        WIN.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT/2 - game_over_text.get_height() - 30))
        WIN.blit(final_score_text, (10,10))
        WIN.blit(current_round, (WIN.get_width() - round.get_width() - 10, 10))
        WIN.blit(restart_text1, (WIDTH//2 - restart_text1.get_width()//2, HEIGHT//2 + game_over_text.get_height()))
        WIN.blit(restart_text2, (WIDTH//2 - restart_text2.get_width()//2, HEIGHT//2 + restart_text1.get_height() + game_over_text.get_height()))
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    exit(0)
                elif event.key == pygame.K_RETURN:
                    running = True
                    start_game_loop()
    

PREVIOUS = 25
previous = []

# Takes in the score player just had and updates database if it's a new high score
# Returns true if they had a new high score and false if they didn't 

def update_high_score(score):
    query = "SELECT * FROM BCI_users WHERE name = %s AND high_score < %s"
    vals = (username, score)

    cursor.execute(query, vals)

    query_return = cursor.fetchall()

    if len(query_return) > 0:
        query = "UPDATE `BCI_users` SET `high_score`= %s WHERE name = %s"
        vals = (score,username)

        cursor.execute(query, vals)
        mydb.commit()
        
        return True
    
    return False 

def leaderboard():
    query = "SELECT * FROM BCI_users"
    cursor.execute(query,)
    query_return = cursor.fetchall()

    return query_return

def ai_analysis_thread():
    global ai_blink_timestamps, blink_calls
    global connected

    MAX_SAMPLES = 24
    WINDOW_SIZE = 5
    BLINK_RADIUS = 0.25
    DEJITTER = True

    # find stream
    print("looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise Exception("Can't find EEG stream")
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=MAX_SAMPLES)
    eeg_time_correction = inlet.time_correction()
    print("looking for a Markers stream...")
    marker_streams = resolve_byprop('type', 'Markers', timeout=2)
    if marker_streams:
        inlet_marker = StreamInlet(marker_streams[0])
        marker_time_correction = inlet_marker.time_correction()
    else:
        inlet_marker = False
        print("Can't find Markers stream")

    # code will only pass to here if stream is found
    connected = True

    # get basic information
    info = inlet.info()
    SAMPLING_FREQUENCY = info.nominal_srate(); assert SAMPLING_FREQUENCY == 256
    SAMPLES_COUNT = int(SAMPLING_FREQUENCY * WINDOW_SIZE)
    CHANNELS_COUNT = info.channel_count()

    # bandpass filter from 1 Hz to 40 Hz (i don't really understand this)
    BANDPASS_FILTER = firwin(32, np.array([1, 40]) / (SAMPLING_FREQUENCY / 2.), width=0.05, pass_zero=False)
    FEEDBACK_COEFFICIENTS = [1.0]
    INITIAL_FILTER = lfilter_zi(BANDPASS_FILTER, FEEDBACK_COEFFICIENTS)
    filter_state = np.tile(INITIAL_FILTER, (CHANNELS_COUNT, 1)).transpose()

    # set up lists for data streams
    times = np.arange(-WINDOW_SIZE, 0, 1/SAMPLING_FREQUENCY)
    data = np.zeros((SAMPLES_COUNT, CHANNELS_COUNT))
    data_filtered = np.zeros((SAMPLES_COUNT, CHANNELS_COUNT))

    model = tf.keras.models.load_model('usingmuselsl/epic_ai_v12.keras')
    while True:
        samples, timestamps = inlet.pull_chunk(timeout=0.05, max_samples=MAX_SAMPLES)
        if timestamps:
            if DEJITTER:
                timestamps = np.float64(np.arange(len(timestamps)))
                timestamps /= SAMPLING_FREQUENCY
                timestamps += times[-1] + 1. / SAMPLING_FREQUENCY

            # add new timestamps to times list
            times = np.concatenate([times, np.atleast_1d(timestamps)])
            SAMPLES_COUNT = int(SAMPLING_FREQUENCY * WINDOW_SIZE)
            # remove old timestamps from the front of times
            times = times[-SAMPLES_COUNT:]

            # add new samples to data list
            data = np.vstack([data, samples])
            # remove old samples from the fromt of data
            data = data[-SAMPLES_COUNT:]

            # filter out noise
            filt_samples, filter_state = lfilter(BANDPASS_FILTER, FEEDBACK_COEFFICIENTS, samples, axis=0, zi=filter_state)

            # add new filtered data to data_filtered
            data_filtered = np.vstack([data_filtered, filt_samples])
            # remove old filtered data from the front of data_filtered
            data_filtered = data_filtered[-SAMPLES_COUNT:]

            # evaluate AI
            data = data_filtered[-CHUNK_LENGTH:]
            data_truncated = np.delete(data, -1, axis=1)

            prediction = model.predict(np.array([data_truncated]), verbose=0)

            if prediction[0][0] >= BLINK_THRESHOLD:
                # adjust for delay MAYBE
                ai_blink_timestamps.append(times[-1])
                blink_calls.append("blink")
            else:
                blink_calls.append("no blink")
        else:
            sleep(0.05)

if USE_BLINK_DETECTION:
    ai_thread = Thread(target=ai_analysis_thread)
    ai_thread.daemon = True
    ai_thread.start()

main_menu()

