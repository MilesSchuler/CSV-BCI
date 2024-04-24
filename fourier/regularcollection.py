# original from https://shaum.pro/collect-real-time-data-from-muse-2-eeg-with-markers-windows-ad60466cbcff

import numpy as np
import pandas as pd
import random
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInlet, resolve_byprop
from sklearn.linear_model import LinearRegression
default_fname = ("data/data_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime())) # make sure to create a folder called 'data' for it to go in
parser = OptionParser()
parser.add_option("-d", "--duration",
                  dest="duration", type='int', default=15, # default is the duration of the recording
                  help="duration of the recording in seconds.")
parser.add_option("-f", "--filename",
                  dest="filename", type='str', default=default_fname,
                  help="Name of the recording file.")
# dejitter timestamps
dejitter = False
(options, args) = parser.parse_args()
print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise(RuntimeError, "Cant find EEG stream")
print("Start aquiring data")
inlet = StreamInlet(streams[0], max_chunklen=12)
eeg_time_correction = inlet.time_correction()
print("looking for a Markers stream...")
marker_streams = resolve_byprop('type', 'Markers', timeout=2)
if marker_streams:
    inlet_marker = StreamInlet(marker_streams[0])
    marker_time_correction = inlet_marker.time_correction()
else:
    inlet_marker = False
    print("Cant find Markers stream")
info = inlet.info()
description = info.desc()
freq = info.nominal_srate()
Nchan = info.channel_count()
ch = description.child('channels').first_child()
ch_names = [ch.child_value('label')]
for i in range(1, Nchan):
    ch = ch.next_sibling()
    ch_names.append(ch.child_value('label'))

# Word Capturing    
currentWord = 1
currentTerm = "HELLO"
t_word = time() + 1 * 2 # the stimulus changes every 2 seconds
words = []
terms = []
termBank = ["WORLD"] # feel free to use your own!
res = []
timestamps = []
markers = []
t_init = time()
print('Start recording at time t=%.3f' % t_init)
print(currentTerm)
while (time() - t_init) < options.duration:
 # Check for new word
    if time() >= t_word:
        currentTerm = random.choice(termBank)
        print("\n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n" + str(currentWord) +": " +currentTerm)
        currentWord += 1
        t_word = time() + 1 * 2
    try:
        data, timestamp = inlet.pull_chunk(timeout=1.0, max_samples=12)
        if timestamp:
            res.append(data)
            timestamps.extend(timestamp)
            words.extend([currentWord] * len(timestamp))
            terms.extend([currentTerm] * len(timestamp))
        if inlet_marker:
            marker, timestamp = inlet_marker.pull_sample(timeout=0.0)
            if timestamp:
                markers.append([marker, timestamp])
    except KeyboardInterrupt:
        break
res = np.concatenate(res, axis=0)
timestamps = np.array(timestamps)
if dejitter:
    y = timestamps
    X = np.atleast_2d(np.arange(0, len(y))).T
    lr = LinearRegression()
    lr.fit(X, y)
    timestamps = lr.predict(X)
res = np.c_[timestamps, words, terms, res]
data = pd.DataFrame(data=res, columns=['timestamps'] + ['words'] + ['terms'] + ch_names)
data['Marker'] = 0
# process markers:
for marker in markers:
    # find index of margers
    ix = np.argmin(np.abs(marker[1] - timestamps))
    val = timestamps[ix]
    data.loc[ix, 'Marker'] = marker[0][0]
data.to_csv(options.filename, float_format='%.3f', index=False)
print('Done !')
print(default_fname)