import numpy as np
import pygame
from pylsl import StreamInlet, resolve_byprop

# Assuming these values for your setup
SAMPLING_RATE = 256
NUM_POINTS = 1024
FREQ_RANGE = (0, 50000)  # Hz
SOUND_VOLUME = 0.5

# Initialize Pygame
pygame.init()
clock = pygame.time.Clock()

# Setup Pygame audio
pygame.mixer.init()

print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise Exception("Can't find EEG stream")
print("Start acquiring data")
inlet = StreamInlet(streams[0], max_chunklen=12)

# Buffer for the last 1000 data points
data_buffer = list(np.zeros((1000,)))

music_playing = False

while True:
    data, timestamp = inlet.pull_chunk(timeout=0.05, max_samples=1)
    if timestamp:
        data = np.array(data).T

        # Update the data buffer
        data_buffer.extend(list(data[0]))

        # Perform FFT on the data buffer
        fft_data = np.fft.fft(data_buffer[-100:], n=NUM_POINTS, axis=0)
        freqs = np.fft.fftfreq(NUM_POINTS, d=1/SAMPLING_RATE)

        # Filter FFT data within frequency range
        mask = (freqs >= FREQ_RANGE[0]) & (freqs <= FREQ_RANGE[1])
        freqs = freqs[mask]
        fft_data = fft_data[mask]

        # Calculate pitch from the FFT data
        pitch = int((np.argmax(np.abs(fft_data)) / len(freqs)) * 1000) + 100

        # Play the pitch as a sound
        if not music_playing:
            pygame.mixer.music.set_volume(SOUND_VOLUME)
            sound_array = np.sin(2 * np.pi * np.arange(44100) * pitch / 44100).astype(np.float32)
            sound_array = np.stack((sound_array, sound_array), axis=-1)  # Make stereo
            sound = pygame.sndarray.make_sound(sound_array)
            sound.play(-1)
            music_playing = True

    clock.tick(30)  # Limit to 30 FPS

# Cleanup
pygame.mixer.quit()
pygame.quit()
