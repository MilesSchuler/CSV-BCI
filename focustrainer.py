from LiveCollectionData.muse_utility import stream, list_muses
import asyncio
from time import sleep
from pylsl import resolve_byprop
from threading import Thread
from LiveCollectionData.streamer import Streamer
from muselsl.constants import LSL_SCAN_TIMEOUT
import csv
import sys

def start_stream_thread(address):
    print("Thread Started")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream(address=address))
    loop.close()

def begin_collecting():

    with open("data.csv", "w") as file:
        writer = csv.writer(file)

        def write_data(data, timestamp):
            writer.writerow([timestamp] + data)

        muse_address = list_muses()[0]['address']
        streaming_thread = Thread(name="Streaming Thread", target=start_stream_thread, args=(muse_address,))
        streaming_thread.start()

        sleep(10.)

        print("Done sleeping.")

        streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
        if len(streams) == 0:
            raise(RuntimeError("Can't find EEG stream."))
        print("Start acquiring data.")

        streamer = Streamer(streams[0], write_data)
        streamer.start(1/10)

        input("Press Enter to stop...")
        streamer.stop()
        print("Ended collection.")
        file.close()

begin_collecting()
sys.exit()