import time
import pygame
import muselsl
import numpy as np 

import matplotlib.pyplot as plt

import csv

from muse_lsl_master.muselsl import stream, list_muses
import asyncio
from time import sleep
from pylsl import resolve_byprop
from threading import Thread
from LiveCollectionData.streamer import Streamer

from muse_lsl_master.muselsl import record 
 
from muselsl.constants import LSL_SCAN_TIMEOUT
# import fictional_eeg_lib  # Uncomment and replace with actual EEG library


def collect_brain_data(duration_seconds):
    # This function should be implemented based on your EEG device and library
    print("Starting brain data collection for {} seconds...".format(duration_seconds))
    # Begin collection logic here
    # e.g., fictional_eeg_lib.start_collection()
    time.sleep(duration_seconds)  # Simulate data collection duration
    # End collection logic here
    # e.g., fictional_eeg_lib.stop_collection()
    print("Brain data collection complete.")

def start_stream_thread(address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))

def setStream():
    muse_address = list_muses()[0]['address']
    streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread, args=(muse_address,))
    streaming_thread.start()

    sleep(10.)

    streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
    if len(streams) == 0:
        raise(RuntimeError("Can't find EEG stream."))

    print("Start acquiring data.")

    streamer = Streamer(streams[0], print) ##Need the function that is going to process the data
    print("Got the streamer.")

    return streamer

setStream() 
record(5)

rows = []

filename = 'example_data.csv'
with open(filename, 'r') as file:
    csvreader = csv.reader(file)
    header = next(csvreader)

    for row in csvreader:
        rows.append(row)



