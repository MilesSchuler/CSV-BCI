CHUNK_LENGTH = 1
CHUNK_OVERLAP = CHUNK_LENGTH - 1
BLINK_THRESHOLD = 0.95
OUTPUT_SIZE = 5

def chunk_generator(arr, length, overlap):
    chunks = []
    for i in range(0, len(arr), length - overlap):
        chunks.append(arr[i:i + length])
    if len(chunks[-1]) < length:
        chunks.pop()
    return chunks

if __name__ == "main":
    print(chunk_generator([[1,1,1,1], [2,2,2,2], [3,3,3,3], [4,4,4,4], [5,5,5,5], [6,6,6,6], [7,7,7,7], [8,8,8,8]], 4, 1))