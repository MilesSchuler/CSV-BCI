CHUNK_LENGTH = 150
CHUNK_OVERLAP = CHUNK_LENGTH - 1
BLINK_THRESHOLD = 0.95

def chunk_generator(arr, length, overlap):
    for i in range(0, len(arr), length - overlap):
        yield arr[i:i + length]