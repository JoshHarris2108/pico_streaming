import ctypes
import time
import matplotlib.pyplot as plot
import numpy as np
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok

class PicoDevice():
    def __init__(self, handle, resolution, buffer_size, num_buffers, auto_stop, auto_stop_stream):

        self.running = True

        self.pico_buffer = (np.zeros((buffer_size,), dtype='int16'))
        self.handle = ctypes.c_int16(handle)
        self.auto_stop = auto_stop
        self.auto_stop_stream = auto_stop_stream

        self.callbackFuncPtr = ps.StreamingReadyType(self.streaming_callback)
        self.status = {}

        self.num_buffers = num_buffers
        self.buffer_size = buffer_size
        self.total_samples = (self.num_buffers * self.buffer_size)

        self.next_sample = 0
        self.captured_samples = 0
        self.called_back = False        

        res = ps.PS5000A_DEVICE_RESOLUTION[resolution]
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, res)
        print(self.status)
    # re-usable function to set up different channels
    def set_channel(self, status_Name, chan, en, coup, range, offset):
        channel_range = ps.PS5000A_RANGE[range]
        channel = ps.PS5000A_CHANNEL[chan]
        coupling = ps.PS5000A_COUPLING[coup]
        self.status[status_Name] = ps.ps5000aSetChannel(self.handle, channel, en, coupling, channel_range, offset)
        print(self.status)

    # re-usable function to set up different buffers for channels
    def set_data_buffer(self, status_Name, chan,segment, rat):
        channel = ps.PS5000A_CHANNEL[chan]
        ratio = ps.PS5000A_RATIO_MODE[rat]
        self.status[status_Name] = ps.ps5000aSetDataBuffers(self.handle, channel, self.pico_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),None, 
                                    self.buffer_size, segment, ratio)
        print(self.status)
    
    # tells the picoscope to start collecting data 
    def run_streaming(self, status_name, samp_int, samp_unit, pre_trig_samp, down_samp_rat, rat):
        sample_int = ctypes.c_int32(samp_int)
        sample_unit = ps.PS5000A_TIME_UNITS[samp_unit]
        ratio = ps.PS5000A_RATIO_MODE[rat]
        self.status[status_name] = ps.ps5000aRunStreaming(self.handle, ctypes.byref(sample_int), sample_unit,pre_trig_samp, self.total_samples, 
                                    self.auto_stop, down_samp_rat, ratio, self.buffer_size)
        print(self.status)

    # 
    def streaming_callback(self, handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
        self.captured_samples += noOfSamples
        self.called_back = True
        print("called_back with data: ",self.pico_buffer)

        
        print("captured_samples: ",self.captured_samples)
    
    def callback_loop(self):
        while self.captured_samples < self.total_samples and not self.auto_stop_stream and self.running:
            self.called_back = False
            self.status["getStreamingLastestValues"] = ps.ps5000aGetStreamingLatestValues(self.handle, self.callbackFuncPtr, None)
            print(self.status)

            if not self.called_back:
                print("\nNot called back: No data ready\n")
                time.sleep(0.001)

    def close_device(self):
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)
        print(self.status)
    

