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
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP, BLINK_THRESHOLD, chunk_generator

PREVIOUS = 25
previous_xs = []

loaded_model = tf.keras.models.load_model('data_test_with_validation.keras')

def start_stream_thread(address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))

def analyze_muse(data, timestamp):
    global previous_xs
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
                    print(prediction[1])
                    print("blink")

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