import numpy as np
import pandas as pd
import os
from typing import Union, List, Optional
from pathlib import Path
from pylsl import StreamInlet, resolve_byprop
from sklearn.linear_model import LinearRegression
from time import time, strftime, gmtime
from muselsl.stream import find_muse
from muselsl import backends
from muselsl.muse import Muse
from muselsl.constants import LSL_SCAN_TIMEOUT, LSL_EEG_CHUNK, LSL_PPG_CHUNK, LSL_ACC_CHUNK, LSL_GYRO_CHUNK
from datetime import datetime
import csv

import pygame 
pygame.mixer.init()

metronome = pygame.mixer.Sound('muse_lsl_master/muselsl/metronome_click.wav')

# Records a fixed duration of EEG data from an LSL stream into a CSV file


def record(
    duration: int,
    filename=None,
    dejitter=False,
    data_source="EEG",
    continuous: bool = True,
) -> None:
    chunk_length = LSL_EEG_CHUNK
    if data_source == "PPG":
        chunk_length = LSL_PPG_CHUNK
    if data_source == "ACC":
        chunk_length = LSL_ACC_CHUNK
    if data_source == "GYRO":
        chunk_length = LSL_GYRO_CHUNK

    if not filename:
        filename = os.path.join(os.getcwd(), "%s_recording_%s.csv" %
                                (data_source,
                                 strftime('%Y-%m-%d-%H.%M.%S', gmtime())))

    print("Looking for a %s stream..." % (data_source))
    streams = resolve_byprop('type', data_source, timeout=LSL_SCAN_TIMEOUT)

    if len(streams) == 0:
        print("Can't find %s stream." % (data_source))
        return

    print("Started acquiring data.")
    inlet = StreamInlet(streams[0], max_chunklen=chunk_length)
    # eeg_time_correction = inlet.time_correction()

    print("Looking for a Markers stream...")
    marker_streams = resolve_byprop(
        'name', 'Markers', timeout=LSL_SCAN_TIMEOUT)

    if marker_streams:
        inlet_marker = StreamInlet(marker_streams[0])
    else:
        inlet_marker = False
        print("Can't find Markers stream.")

    info = inlet.info()
    description = info.desc()

    Nchan = info.channel_count()

    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, Nchan):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))
    

    t_init = time()
    time_correction = inlet.time_correction()
    
    print('Start recording at time t=%.3f' % t_init)
    print('Time correction: ', time_correction)

    blink_time = time() + 1

    iteration = 1

    filename = str(datetime.now())
    # colons are reserved characters so can't be used in a file name
    filename = filename.replace(':', '.')

    while (time() - t_init) < duration:
        try:
            blink = False
            if(blink_time <= time()):
                if(time() >= blink_time + 0.2):
                    print("blink now")
                    metronome.play()
                    blink_time = time() + 1
                blink = True 


            data, timestamp = inlet.pull_chunk(
                timeout=1.0, max_samples=chunk_length)
            
            rows = []

            for i in range(0, len(data)):
                chunk = []

                chunk.append(timestamp[i])

                for k in range(0, 4):
                    chunk.append(data[i][k])
            
                chunk.append(blink)

                rows.append(chunk)
                
            

            if(iteration == 1):
                with open(filename, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "Sensor 1", "Sensor 2", 'Sensor 3', "Sensor 4", "Blink"])
                    writer.writerows(rows)
            else:
                with open(filename, 'a') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)
            
            iteration+=1

        except KeyboardInterrupt:
            break

    time_correction = inlet.time_correction()
    print("Time correction: ", time_correction)

    print("Done - wrote file: {}".format(filename))
    


# Rercord directly from a Muse without the use of LSL


def record_direct(duration,
                  address,
                  filename=None,
                  backend='auto',
                  interface=None,
                  name=None):
    if backend == 'bluemuse':
        raise (NotImplementedError(
            'Direct record not supported with BlueMuse backend. Use record after starting stream instead.'
        ))

    if not address:
        found_muse = find_muse(name, backend)
        if not found_muse:
            print('Muse could not be found')
            return
        else:
            address = found_muse['address']
            name = found_muse['name']
        print('Connecting to %s : %s...' % (name if name else 'Muse', address))

    if not filename:
        filename = os.path.join(
            os.getcwd(),
            ("recording_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime())))

    eeg_samples = []
    timestamps = []

    def save_eeg(new_samples, new_timestamps):
        eeg_samples.append(new_samples)
        timestamps.append(new_timestamps)

    muse = Muse(address, save_eeg, backend=backend)
    muse.connect()
    muse.start()

    t_init = time()
    print('Start recording at time t=%.3f' % t_init)

    while (time() - t_init) < duration:
        try:
            backends.sleep(1)
        except KeyboardInterrupt:
            break

    muse.stop()
    muse.disconnect()

    timestamps = np.concatenate(timestamps)
    eeg_samples = np.concatenate(eeg_samples, 1).T
    recording = pd.DataFrame(
        data=eeg_samples, columns=['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX'])

    recording['timestamps'] = timestamps

    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    recording.to_csv(filename, float_format='%.3f')
    print('Done - wrote file: ' + filename + '.')


record(240)