# like before, need to start the muselsl stream elsewhere first

import keyboard
import time
import csv
from datetime import datetime
from bisect import bisect_left
import muselsl 
from muselsl import record, stream, list_muses
from muselsl.constants import LSL_SCAN_TIMEOUT, LSL_EEG_CHUNK
from pylsl import StreamInlet, resolve_byprop
import threading
from pynput.keyboard import Key, Listener
import os

data = []
timestamps = []

user = input("User: (Amy, Miles, Yitbrek, NA) ")
if user == "NA":
    FILENAME = "Tetris " + str(datetime.now()).replace(':', '.') + ".csv"
else:
    FILENAME = "Tetris Data " + user + ".csv"

total_seconds = int(input("Total seconds of data collection: "))
end_time = time.time() + total_seconds

## CHANGE THIS TO ALTER HOW MANY SECONDS BETWEEN DIRECTIONAL THOUGHT COMPUTER SHOULD READ 
TIME_BETWEEN_THOUGHT = 0.1

chunk_length = LSL_EEG_CHUNK
data_source = "EEG"

def collect_data(inlet, data, timestamps):
    global end_time


    while end_time > time.time():
        chunk_data, chunk_timestamps = inlet.pull_chunk(timeout=5, max_samples=30000)
        data.extend(chunk_data)
        timestamps.extend(chunk_timestamps)

        time.sleep(1)
    
    print("Data collection finished.")
    keyboard.press('esc')
    keyboard.release('esc')

def record_keys():
    key_events = []
    start_time = time.time()
    global do_keep_recording

    def on_press(key):
        check_key(key)

    def on_release(key):
        if key == Key.esc:
            # Stop listener
            return False

    def check_key(key):
        # converting to smth like 'up' rather than 'key.up', etc
        key_str = str(key)[slice(4,len(str(key)))]
        if key_str in ['up','down','left','right']: 
            key_events.append((time.time(), key_str))
            # so we know it's working
            print(str(time.time()) + ": " + key_str)

    # Collect events until released
    with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
        thread

    

    return key_events, start_time

if __name__ == "__main__":

    ## Start collecting brain data 
    streams = resolve_byprop('type', data_source, timeout=LSL_SCAN_TIMEOUT)
    inlet = StreamInlet(streams[0], max_chunklen=chunk_length)
    thread = threading.Thread(target=collect_data, args=(inlet, data, timestamps), daemon=True)
    thread.start()


    print("Recording key inputs.")
    key_events, start_time = record_keys()
    print("Key inputs recorded.")

    # Wait for the data collection threads to finish
    thread.join()


    ## 
    lengthOfWave = TIME_BETWEEN_THOUGHT

    key_presses = 0

    with open(FILENAME, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['timestamp', 'key'])
        for timestamp, key in key_events:
            csvwriter.writerow([timestamp, key])
            key_presses += 1

    ## Iterate through all the points from the EEG 
    filename = FILENAME
    file = open(filename)
    csvreader = csv.reader(file)
    next(csvreader)


    rows = [] 
    for row in csvreader:
        rows.append(row)
    
    for row in data: 
        row.append('none')

    
    for row in rows:  
        key_time = row[0]
        key = row[1]
        
        min_time = float(key_time) - lengthOfWave
        max_time = float(key_time) + lengthOfWave

        index = 0 

        for timestamp in timestamps:
            timestamp = float(timestamp)
            if timestamp >= min_time and timestamp <= max_time:
                data[index][-1] = key 

            index+=1
    
    index = 0
    for row in data: 
        row.insert(0, str(timestamps[index]))
        index+=1
    
    rows = data

    if os.path.exists(FILENAME):
        mode = 'a'  # Append mode if the file already exists
    else:
        mode = 'w'  # Write mode if the file doesn't exist

    with open(filename, mode, newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        if mode == 'w':
            column_names = ['Timestamp', 'Sensor 1', 'Sensor 2', 'Sensor 3', 'Sensor 4', 'Sensor 5', 'Direction']
            csvwriter.writerow(column_names)
        for timestamp, key in key_events:
            csvwriter.writerows(rows)


    # really janky temp fix
    rows_to_keep = []

    with open(FILENAME, 'r', newline='') as csvfile:
        csvwriter = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            if index >= key_presses:
                rows_to_keep.append(row)
    
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(rows_to_keep)
        

    # Save recorded data to a file

    print("Data recorded and saved: " + filename)