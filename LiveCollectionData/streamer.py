from pylsl import StreamInlet
from threading import Timer
from muselsl.constants import LSL_EEG_CHUNK

class Streamer():
    def __init__(self, stream, target):
        self.inlet = StreamInlet(stream, max_chunklen=LSL_EEG_CHUNK)
        self.target = target

    def start(self, interval):
        Timer(interval, self.start, args=(interval,)).start()
        samples, timestamps = self.get_data()
        self.target(samples, timestamps)

    def get_data(self):
        samples, timestamps = self.inlet.pull_chunk(timeout=1.0, max_samples=1)#LSL_EEG_CHUNK)
        return samples, timestamps