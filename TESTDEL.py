def chunk_generator(arr, n, w):
    for i in range(0, len(arr), n - w):
        yield arr[i:i + n]

# Example array
arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Chunk size
n = 4

# Overlap
w = 3

# Iterate over each chunk
for chunk in chunk_generator(arr, n, w):
    print(chunk)
