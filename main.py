import queue
import signal
import threading
import ctypes
#import time
import numpy as np

from producer import Producer
from consumer import Consumer
from pico import PicoDevice


class StreamExample():

    def __init__(self):

        data_queue = queue.Queue()
        empty_queue = queue.Queue()
        buffer_size = 25600
        num_buffers = 120
        data_buffers = []
        auto_stop = 1
        auto_stop_stream = False
        # buffer_size and num_buffers need to be moved elsewhere 
        self.pico_device = PicoDevice(0,"PS5000A_DR_12BIT",buffer_size, num_buffers)
        self.pico_device.set_channel('setChA','PS5000A_CHANNEL_A',1,'PS5000A_DC','PS5000A_20V',0.0)
        self.pico_device.set_data_buffer('setDataBufferA','PS5000A_CHANNEL_A',0,'PS5000A_RATIO_MODE_NONE')
        # call a funciton that sets the run_streaming variables up, but doesnt actually call the 
        # run streaming 
        self.pico_device.configure_streaming(32,'PS5000A_NS',0,1,'PS5000A_RATIO_MODE_NONE',auto_stop, auto_stop_stream)
        




        file_name = 'data.npy' #not in use

        # Creates an empty_queue that stores the indexes of empty buffers
        # The buffers are created as empty buffers and all added to the empty 
        # queue ready to be filled with data by the producer
        for idx in range(num_buffers):
            data_buffers.append(np.empty((buffer_size,), dtype='int16'))
            empty_queue.put(idx)
        
        #self.producer = Producer(buffer_size,data_queue,empty_queue,data_buffers)
        #self.consumer = Consumer(buffer_size,data_queue,empty_queue,data_buffers,file_name)
        self.pico_thread = threading.Thread(target=self.pico_device.callback_loop)

        #self.producer_thread = threading.Thread(target=self.producer.produce)
        #self.consumer_thread = threading.Thread(target=self.consumer.consume)

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("Shutting down")
        #self.producer.stop()
        #self.consumer.stop()
        self.pico_device.running = False
        self.pico_device.close_device()

    def run(self):

        #self.producer_thread.start()
        #self.consumer_thread.start()

        #self.producer_thread.join()
        #self.consumer_thread.join()
        self.pico_thread.start()
        self.pico_thread.join()


if __name__ == '__main__':

    streamer = StreamExample()
    streamer.run()
