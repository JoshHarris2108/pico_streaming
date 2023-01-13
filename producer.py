import queue
import time
import numpy as np

class Producer():
    def __init__(self, buffer_size, data_queue, empty_queue, data_buffers):
        self.buffer_size = buffer_size
        self.data_queue = data_queue
        self.empty_queue = empty_queue
        self.data_buffers = data_buffers
        self.running = True

        self.space_left = self.buffer_size
        self.overflow = np.empty(0,dtype='int16')

        ## Keep track of space_left in here
        ## have a array_overflow that can be then added to the 
        ## do check in the producer while loop for the space_left being negative 
        ## if its negative, add the contents of array_overflow to the beginning of 
        ## the next array being appended 

    def stop(self):
        self.running = False

    def produce(self):
        total_data_length = 0
        a = 0
        while self.running:
            print("\nIteration of main while loop: ",a)
            time.sleep(1)

            # reset the space_left each time a new empty_queue index is recieved 
            self.space_left = self.buffer_size # Does this need to be a self. variable?

            try:
                # get data buffer index that is now "empty"
                idx = self.empty_queue.get(timeout=0.1)
                # check if self.overflow has any values
                if (len(self.overflow) != 0):
                    print("Entering overflow condition on iteration: ",a)
                    print("Contents of overflow: ",self.overflow)
                    self.data_buffers[idx] = np.append(self.data_buffers[idx],self.overflow)
                    print("producer queueing overflow to idx", idx)
                    self.space_left -= len(self.overflow)
                    total_data_length += len(self.overflow)
                    #reset overflow here

                while self.space_left > 0:
                    # generate data that varies in length
                    data = np.random.randint(1,high=10000, size=(np.random.randint(4,high=12, size=1)), dtype='int16')
                    print("Generated data: ",data," Of length: ", len(data))
                    # check data is not bigger than space left in current buffer
                    if self.space_left >= len(data):
                        #append data to buffer
                        self.data_buffers[idx] = np.append(self.data_buffers[idx],data)
                        self.space_left -= len(data)
                        print("Space left in buffer: ",idx," = ",self.space_left)
                        total_data_length += len(data)
                    else:
                        # appends the data that will fit into the current buffer (filling it up to its set size e.g 2560 values)
                        sub_array = data[0:self.space_left]
                        self.data_buffers[idx] = np.append(self.data_buffers[idx],sub_array)
                        total_data_length += len(sub_array)

                        
                        print("length of final append: ",(len(sub_array)))
                        print("Space left after final append: ",self.space_left)

                        #stores the left over data in self.overflow
                        self.overflow = data[self.space_left:len(data)]
                        self.space_left -= len(sub_array)
                        print("Length of overflow: ", len(self.overflow))
                        print("\n\n",self.data_buffers[idx], "\nbuffer length: ",len(self.data_buffers[idx]))

                # puts the data buffer index onto the queue for the consumer to write the buffer contents
                self.data_queue.put(idx)

            except queue.Empty:
                print("empty_queue is empty")
                #break                
                time.sleep(0.01)
            a += 1
            # if idx == 2:
            #     print("\n\n")
            #     for i in range (len(self.data_buffers)):
            #         print(self.data_buffers[i])
            #     print("data generation finished", total_data_length)
            #     self.running = False
                

                

        
            
        

        ############## END OF self.running WHILE LOOP ####################

        

        
