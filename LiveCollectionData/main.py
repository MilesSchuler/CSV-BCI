from muse_utility import stream, list_muses
import asyncio
from time import sleep
from pylsl import resolve_byprop
from threading import Thread
from streamer import Streamer

from muselsl.constants import LSL_SCAN_TIMEOUT

def start_stream_thread(address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))

muse_address = list_muses()[0]['address']
streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread, args=(muse_address,))
streaming_thread.start()

sleep(10.)

streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
if len(streams) == 0:
    raise(RuntimeError("Can't find EEG stream."))
print("Start acquiring data.")

streamer = Streamer(streams[0], print)
streamer.start(1.0)