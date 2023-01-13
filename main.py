import queue
import signal
import threading
#import time
import numpy as np

from producer import Producer
from consumer import Consumer


class StreamExample():

    def __init__(self):

        data_queue = queue.Queue()
        empty_queue = queue.Queue()
        buffer_size = 30
        num_buffers = 3
        data_buffers = []
        file_name = 'data.npy' #not in use atm

        # Creates an empty_queue that stores the indexes of empty buffers
        # The buffers are created as empty buffers and all added to the empty 
        # queue ready to be filled with data by the producer
        for idx in range(num_buffers):
            data_buffers.append(np.empty(0,dtype='int16'))
            empty_queue.put(idx)
        
        self.producer = Producer(buffer_size,data_queue,empty_queue,data_buffers)
        self.consumer = Consumer(buffer_size,data_queue,empty_queue,data_buffers,file_name)

        self.producer_thread = threading.Thread(target=self.producer.produce)
        self.consumer_thread = threading.Thread(target=self.consumer.consume)

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("Shutting down")
        self.producer.stop()
        self.consumer.stop()

    def run(self):

        self.producer_thread.start()
        self.consumer_thread.start()

        self.producer_thread.join()
        self.consumer_thread.join()


if __name__ == '__main__':

    streamer = StreamExample()
    streamer.run()
