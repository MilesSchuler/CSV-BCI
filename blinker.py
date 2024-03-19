from LiveCollectionData.muse_utility import stream, list_muses
import asyncio
from time import sleep
from pylsl import resolve_byprop
from threading import Thread
from LiveCollectionData.streamer import Streamer
from muselsl.constants import LSL_SCAN_TIMEOUT
import sys
import numpy as np

PREVIOUS = 25
previous_xs = []


def start_stream_thread(address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))

def chunk_generator(arr, n, w):
    for i in range(0, len(arr), n - w):
        yield arr[i:i + n]

def analyze_muse(data, timestamp):

    checkable_x = []

    for row in data:
        input = [
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4])
        ]

        previous_xs.append(input)

        if len(previous_xs) > PREVIOUS:
            previous_xs.pop(0)
            checkable_x.append(np.array(previous_xs).flatten())

    print(len(checkable_x))

    sys.exit()
    for datum in data:
        datum = datum[:4]
        PREVIOUS.append(datum)

    # arr, size, overlap
    for chunk in chunk_generator(PREVIOUS, 40, 20):
        print(np.array(chunk[0]))
        sys.exit()

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