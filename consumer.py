import queue
import h5py
import time
import numpy as np

class Consumer:
    def __init__(self, buffer_size, data_queue, empty_queue, data_buffers,file_name):
        self.buffer_size = buffer_size
        self.data_queue = data_queue
        self.empty_queue = empty_queue
        self.data_buffers = data_buffers
        self.file_name = file_name
        self.running = True

        self.values_written = 0

        self.cmaxSamples = 0
        self.timeIntervalns = 0
        self.chARange = 0
        self.maxADC = 0

        self.empty_con_queue_count = 0

    def set_metadata(self,cmaxSamples,timeIntervalns,chARange,maxADC):
        self.cmaxSamples = cmaxSamples
        self.timeIntervalns = timeIntervalns
        self.chARange = chARange
        self.maxADC = maxADC

    def stop(self):
        self.running = False
    
    def consume(self):
        total_save_length = 0
        metadata = {
            'cmaxSamples': 2560,
            'timeIntervalns': 80,
            'chARange': self.chARange,
            'maxADC': self.maxADC
        }
        with h5py.File('/tmp/data.hdf5','w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value

            dset = f.create_dataset('adc_counts',(self.buffer_size,),maxshape=(None,),dtype='int16', chunks=(self.buffer_size,))

            while self.running:
                if not self.running:
                    break
                try:
                    idx = self.data_queue.get(timeout=0.1)

                    dset.resize((self.values_written+(len(self.data_buffers[idx])),))
                    dset[self.values_written:] = self.data_buffers[idx]
                    self.empty_queue.put(idx)

                    self.values_written += len(self.data_buffers[idx])

                except queue.Empty:
                    self.empty_con_queue_count += 1   

        print("Number of times consumer couldnt obtain queue: ", self.empty_con_queue_count)
