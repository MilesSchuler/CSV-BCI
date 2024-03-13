from pylsl import StreamInlet
from threading import Timer
from muselsl.constants import LSL_EEG_CHUNK

class Streamer():
    def __init__(self, stream, target):
        self.inlet = StreamInlet(stream, max_chunklen=LSL_EEG_CHUNK)
        self.target = target
        self.timer = None

    def start(self, interval):
        self.timer = Timer(interval, self._on_timer, args=(interval,))
        self.timer.start()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()

    def _on_timer(self, interval):
        samples, timestamps = self.get_data()
        self.target(samples, timestamps)
        # Restart the timer
        self.timer = Timer(interval, self._on_timer, args=(interval,))
        self.timer.start()

    def get_data(self):
        samples, timestamp = self.inlet.pull_chunk(timeout=1.0, max_samples=LSL_EEG_CHUNK)
        return samples, timestamp
