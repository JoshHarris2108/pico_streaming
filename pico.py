import ctypes
import time
import matplotlib.pyplot as plot
import numpy as np
import queue

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV

class PicoDevice():
    def __init__(self, handle, resolution, pico_buffer_size,pico_num_buffers,comp_buffer_size,data_queue,empty_queue,data_buffers):
        ####### Setup variables #######
        self.handle = ctypes.c_int16(handle)
        res = ps.PS5000A_DEVICE_RESOLUTION[resolution]

        ####### Local picoscope buffer variables #######
        self.pico_buffer_size = pico_buffer_size
        self.pico_num_buffers = pico_num_buffers
        self.total_samples = self.pico_buffer_size*self.pico_num_buffers

        ####### File writing buffer variables #######
        self.comp_buffer_size = comp_buffer_size
    
        ####### Temporary writing buffer variables #######        
        #self.bufferCompA = np.zeros(shape=(self.total_samples), dtype=np.int16)
        self.bufferA = np.zeros(shape=self.pico_buffer_size, dtype=np.int16)

        ####### Misc variables #######
        self.callbackFuncPtr = ps.StreamingReadyType(self.streaming_callback)
        self.channel_range = None
        self.running = True
        ####### Callback Function Variables #######

        self.nextSample = 0
        self.autoStopStream = False
        self.calledBack = False

        self.data_queue = data_queue
        self.empty_queue = empty_queue
        self.data_buffers = data_buffers

        self.buf_idx = self.empty_queue.get()
        self.buf_used = 0
        self.buf_free = self.comp_buffer_size
        
        ####### Streaming Variables #######
        self.sample_int = None
        self.sample_unit = None
        self.ratio = None
        self.pre_trig_samples = None
        self.down_sample_ratio = None
        self.auto_stop = None
        self.auto_stop_stream = None

        ####### Status information #######
        self.status = {}
        self.captured_samples = 0
        self.max_sample = 0
        self.max_sample_point = 0
        self.max_sample_count = 0
        self.empty_pro_queue_count = 0

        ####### Open device conneciton #######
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, res)
    
    def set_channel(self, status_Name, chan, en, coup, range, offset):
        channel_range = ps.PS5000A_RANGE[range]
        self.channel_range = channel_range
        channel = ps.PS5000A_CHANNEL[chan]
        coupling = ps.PS5000A_COUPLING[coup]
        self.status[status_Name] = ps.ps5000aSetChannel(self.handle, channel, en, coupling, channel_range, offset)
        print(self.status)
    
    def set_data_buffer(self, status_Name, chan,segment, rat):
        channel = ps.PS5000A_CHANNEL[chan]
        ratio = ps.PS5000A_RATIO_MODE[rat]
        self.status[status_Name] = ps.ps5000aSetDataBuffers(self.handle, channel, self.bufferA.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),None, 
                                    self.pico_buffer_size, segment, ratio)
        print(self.status)

    def configure_streaming_var(self, samp_int, samp_unit, pre_trig_samp, down_samp_rat, rat, auto_stop, auto_stop_stream):
        self.sample_int = ctypes.c_int32(samp_int)
        self.sample_unit = ps.PS5000A_TIME_UNITS[samp_unit]
        self.ratio = ps.PS5000A_RATIO_MODE[rat]
        self.pre_trig_samples = pre_trig_samp
        self.down_sample_ratio = down_samp_rat
        self.auto_stop = auto_stop
        self.auto_stop_stream = auto_stop_stream

    def run_streaming(self):
        self.status['runStreaming'] = ps.ps5000aRunStreaming(self.handle, ctypes.byref(self.sample_int), self.sample_unit,self.pre_trig_samples, self.total_samples, 
                                    self.auto_stop, self.down_sample_ratio, self.ratio, self.pico_buffer_size)
        print(self.status)

    # this function is called each time data is avaible from the picoscope, from here the data in the buffer should be accessed
    def streaming_callback(self,handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):

        if self.running:
            if (noOfSamples>=self.max_sample):
                self.max_sample = noOfSamples
                self.max_sample_point = self.captured_samples
                self.max_sample_count += 1
            #print("\nCurrent buffer: ",self.buf_idx," Used: ",self.buf_used)
            len_data = noOfSamples
            #len_data = len(self.pico_buffer)
            #print(f"\nNew data length {len_data}")

            src_idx = startIndex

            self.captured_samples += noOfSamples
            self.calledBack = True
            #print("No of samples: ",noOfSamples)
            #print("captured_samples: ",self.captured_samples)


            while len_data > 0:
                self.buf_free = self.comp_buffer_size - self.buf_used
                copy_size = min(len_data, self.buf_free)

                # print(
                #     f">> Copy to buf idx:{self.buf_idx}, used:{self.buf_used}, free:{self.buf_free}, "
                #     f"src:{src_idx} size:{copy_size}, remain:{len_data}"
                # )
                # print(
                #     f">> buffers[{self.buf_idx}][{self.buf_used}:{self.buf_used+copy_size}] = data[{src_idx}:{src_idx+copy_size}]"
                # )

                self.data_buffers[self.buf_idx][self.buf_used:self.buf_used+copy_size] = self.bufferA[src_idx:src_idx+copy_size]

                self.buf_used += copy_size
                len_data -= copy_size
                src_idx += copy_size

                if self.buf_used == self.comp_buffer_size:
                    self.data_queue.put(self.buf_idx)
                    idx_found = True
                    #print(self.buf_idx)
                    while idx_found and self.running:
                        try:
                            self.buf_idx = self.empty_queue.get(timeout=0.1)
                            #print(self.buf_idx)
                            self.buf_used = 0
                            idx_found = False
                        except queue.Empty:
                            self.empty_pro_queue_count += 1
                            #print("\nempty_queue is empty")
    
    def plot_data(self):
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.handle, ctypes.byref(maxADC))

        adc2mVChAMax = adc2mV(self.bufferCompA, self.channel_range, maxADC)
        print('Channel_range: ',self.channel_range)
        timedata = np.linspace(0,((self.total_samples - 1) * self.sample_int.value), self.total_samples)

        plot.plot(timedata, adc2mVChAMax[:])
        plot.xlabel('Time (ns)')
        plot.ylabel('Voltage (mV)')
        plot.show()

    def run_capture(self):        
        start = time.time()
        self.run_streaming()
        while self.running:
            if ((time.time()-start) >= 10):
                self.running = False
            calledBack = False
            self.status["getStreamingLastestValues"] = ps.ps5000aGetStreamingLatestValues(self.handle, self.callbackFuncPtr, None)
            if not calledBack:
                pass
        end = time.time()
        print(end-start)
        print("Number of times producer couldnt obtain queue: ", self.empty_pro_queue_count)
        print("Maximum returned samples: ",self.max_sample)
        print("Latest maximum hit: ", self.max_sample_point)
        print("maximum hit count: ",self.max_sample_count)
        self.close_device()


    def close_device(self):
        self.running = False
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)
        print(self.status)
