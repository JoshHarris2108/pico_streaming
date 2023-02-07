import ctypes
import time
import matplotlib.pyplot as plot
import numpy as np
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok

class PicoDevice():
    def __init__(self, handle, resolution, buffer_size, num_buffers):
        #buffer_size, num_buffers,auto_stop,auto_stop_stream
    
        ############### initialisation variables ###############
        self.handle = ctypes.c_int16(handle)
        res = ps.PS5000A_DEVICE_RESOLUTION[resolution]

        ############### control variables ###############
        self.auto_stop = 1
        self.auto_stop_stream = False
        self.running = True

        ############### state variables ###############
        self.status = {}
        self.called_back = False

        ############### buffer variables ###############
        self.num_buffers = num_buffers
        self.buffer_size = buffer_size
        self.pico_buffer = (np.zeros((self.buffer_size,), dtype='int16'))

        ############### sample variables ###############
        self.total_samples = (self.num_buffers * self.buffer_size)
        self.next_sample = 0
        self.captured_samples = 0

        ############### streaming variables ###############
        self.sample_int = ctypes.c_int32(32)
        self.sample_unit = ps.PS5000A_TIME_UNITS['PS5000A_NS']
        self.ratio = ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_NONE']
        self.pre_trig_samples = 0
        self.down_sample_ratio = 1

        ############### misc variables ###############
        self.callbackFuncPtr = ps.StreamingReadyType(self.streaming_callback)

        # Initalise connection to the picoscope
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
    
    # sets up the parameters for streaming without starting data collection 
    def configure_streaming(self, samp_int, samp_unit, pre_trig_samp, down_samp_rat, rat, auto_stop, auto_stop_stream):
        self.sample_int = ctypes.c_int32(samp_int)
        self.sample_unit = ps.PS5000A_TIME_UNITS[samp_unit]
        self.ratio = ps.PS5000A_RATIO_MODE[rat]
        self.pre_trig_samples = pre_trig_samp
        self.down_sample_ratio = down_samp_rat
        self.auto_stop = auto_stop
        self.auto_stop_stream = auto_stop_stream

    # tells the picoscope to start collecting data based on variables already defined
    def run_streaming(self):
        self.status['runStreaming'] = ps.ps5000aRunStreaming(self.handle, ctypes.byref(self.sample_int), self.sample_unit,self.pre_trig_samples, self.total_samples, 
                                    self.auto_stop, self.down_sample_ratio, self.ratio, self.buffer_size)
        print(self.status)

    # this function is called each time data is avaible from the picoscope, from here the data in the buffer should be accessed
    def streaming_callback(self, handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
        self.captured_samples += noOfSamples
        self.called_back = True
        print("called_back with data: ",self.pico_buffer)
        print("No of samples: ",noOfSamples)
        print("Overflow from picoscope",overflow)
        print("captured_samples: ",self.captured_samples)
    
    def callback_loop(self):
        self.run_streaming()
        while self.captured_samples < self.total_samples and not self.auto_stop_stream and self.running:
            self.called_back = False
            self.status["getStreamingLastestValues"] = ps.ps5000aGetStreamingLatestValues(self.handle, self.callbackFuncPtr, None)
            print(self.status)

            if not self.called_back:
                print("\nNot called back: No data ready\n")
                time.sleep(0.001)
        self.close_device()

    def close_device(self):
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)
        print(self.status)
    
