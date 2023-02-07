import queue
import signal
import threading
import numpy as np

from consumer import Consumer
from pico import PicoDevice


class StreamExample():

    def __init__(self):

        data_queue = queue.Queue()
        empty_queue = queue.Queue()
        buffer_size = 51200000  
        num_buffers = 5
        data_buffers = []

        auto_stop = 0
        auto_stop_stream = False

        file_name = 'data.npy' #not in use

        # Creates an empty_queue that stores the indexes of empty buffers
        # The buffers are created as empty buffers and all added to the empty 
        # queue ready to be filled with data by the producer
        for idx in range(num_buffers):
            data_buffers.append(np.empty((buffer_size,), dtype='int16'))
            empty_queue.put(idx)
        
        self.consumer = Consumer(buffer_size,data_queue,empty_queue,data_buffers,file_name)
        self.pico_device = PicoDevice(0,"PS5000A_DR_12BIT",640000,1,buffer_size,data_queue,empty_queue,data_buffers)
        
        self.pico_device.set_channel('setChA','PS5000A_CHANNEL_A',1,'PS5000A_DC','PS5000A_20V',0.0)
        self.pico_device.set_channel('setChB','PS5000A_CHANNEL_B',0,'PS5000A_DC','PS5000A_20V',0.0)
        self.pico_device.set_channel('setChC','PS5000A_CHANNEL_C',0,'PS5000A_DC','PS5000A_20V',0.0)
        self.pico_device.set_channel('setChD','PS5000A_CHANNEL_D',0,'PS5000A_DC','PS5000A_20V',0.0)
        self.pico_device.set_data_buffer('setDataBufferA','PS5000A_CHANNEL_A',0,'PS5000A_RATIO_MODE_NONE')
        self.pico_device.configure_streaming_var(16,'PS5000A_NS',0,1,'PS5000A_RATIO_MODE_NONE',auto_stop, auto_stop_stream)
        
        self.consumer_thread = threading.Thread(target=self.consumer.consume)
        self.pico_thread = threading.Thread(target=self.pico_device.run_capture)

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("Stopping data acquisition/saving")
        self.consumer.stop()
        self.pico_device.running = False
        self.pico_device.close_device()

    def run(self):
        self.consumer_thread.start()
        self.pico_thread.start()
        self.consumer_thread.join()        
        self.pico_thread.join()


if __name__ == '__main__':

    streamer = StreamExample()
    streamer.run()
