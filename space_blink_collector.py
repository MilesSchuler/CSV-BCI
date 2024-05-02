from pynput.keyboard import Key, Listener
import logging
import threading
import time
import csv 
import pandas as pd 
import os 
import statistics 
          
from CSV_BCI.muse_lsl_master.muselsl import record

blink_times = []
def find_slope(points):

    slopes = []
    ii = 0
    while ii < 4:
        wave = float(points[ii]['Sensor 4'])
        wave_two = float(points[ii+1]['Sensor 4'])

        piece_slope = (wave + wave_two)/2
        slopes.append(piece_slope)
        ii+=1
    
    slope = statistics.mean(slopes)

    return slope 

def thread_function(name):
	with Listener(on_press=on_press, on_release=on_release) as listener:
		listener.join()

def on_press(key):  
	if key == Key.space:
		pressed_time = time.time()

		blink_start = pressed_time - 0.15 
		blink_end = pressed_time + 0.15
		
		blink_times.append([blink_start, blink_end]) 
	
def on_release(key):
	if key == Key.space:
		print("space key relasesed")
	if key == Key.esc:
		# Stop listener
		return False
	

if __name__ == "__main__":
	x = threading.Thread(target=thread_function, args=(1,))
	x.start()        
	filename = record(10)
 
	df = pd.read_csv(filename)

	print(df['timestamps'][0])
		
	blink_identifiers = []
	
	ii = 0 
	while ii < len(df['timestamps']):
		timestamp = df['timestamps'][ii]
		inside_interval = False
		for interval in blink_times:
			if timestamp > interval[0] and timestamp < interval[1]:
				inside_interval = True
		if inside_interval:
			blink_identifiers.append('1')
		else:
			blink_identifiers.append('0')
		ii+=1

				 
	df.insert(2, "Blink", blink_identifiers, True)
	
	df.to_csv(filename, index = False)      
	
	print("finished")  