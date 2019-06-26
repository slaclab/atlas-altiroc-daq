#!/usr/bin/env python3
#################################################################
import sys
import os
import rogue
import time
import random
import argparse
import pyrogue as pr
import pyrogue.gui
import numpy as np
import rogue.utilities.fileio
import statistics
import math
import matplotlib.pyplot as plt


class PixValue(object):
  def __init__(self, PixelIndex, TotOverflow, TotData, ToaOverflow, ToaData, Hit, Sof):
     self.PixelIndex  = PixelIndex
     self.TotOverflow = TotOverflow
     self.TotData     = TotData
     self.ToaOverflow = ToaOverflow
     self.ToaData     = ToaData
     self.Hit         = Hit
     self.Sof         = Sof

class EventValue(object):
  def __init__(self):
     self.FormatVersion     = None
     self.PixReadIteration  = None
     self.StartPix          = None
     self.StopPix           = None
     self.SeqCnt            = None
     self.pixValue          = None

def ParseDataWord(dataWord):
    # Parse the 32-bit word
    PixelIndex  = (dataWord >> 24) & 0x1F
    TotOverflow = (dataWord >> 20) & 0x1
    TotData     = (dataWord >> 11) & 0x1FF
    ToaOverflow = (dataWord >> 10) & 0x1
    ToaData     = (dataWord >>  3) & 0x7F
    Hit         = (dataWord >>  2) & 0x1
    Sof         = (dataWord >>  0) & 0x3
    return PixValue(PixelIndex, TotOverflow, TotData, ToaOverflow, ToaData, Hit, Sof)

#################################################################

class ExampleEventReader(rogue.interfaces.stream.Slave):
    # Init method must call the parent class init
    def __init__(self):
        super().__init__()

    # Method which is called when a frame is received
    def _acceptFrame(self,frame):

        # First it is good practice to hold a lock on the frame data.
        with frame.lock():

            # Next we can get the size of the frame payload
            size = frame.getPayload()
            
            # To access the data we need to create a byte array to hold the data
            fullData = bytearray(size)
            
            # Next we read the frame data into the byte array, from offset 0
            frame.read(fullData,0)

            # Fill an array of 32-bit formatted word
            wrdData = [None for i in range(2+512*32)]
            wrdData = np.frombuffer(fullData, dtype='uint32', count=(size>>2))
            
            # Parse the data and data to data frame
            eventFrame = EventValue()
            eventFrame.FormatVersion     = (wrdData[0] >>  0) & 0xFFF
            eventFrame.PixReadIteration  = (wrdData[0] >> 12) & 0x1FF
            eventFrame.StartPix          = (wrdData[0] >> 22) & 0x1F
            eventFrame.StopPix           = (wrdData[0] >> 27) & 0x1F
            eventFrame.SeqCnt            = wrdData[1]
            numPixValues = (eventFrame.StopPix-eventFrame.StartPix+1)*(eventFrame.PixReadIteration+1)
            eventFrame.pixValue  = [None for i in range(numPixValues)]
            for i in range(numPixValues):
                eventFrame.pixValue[i] = ParseDataWord(wrdData[2+i])
                
            # Print out the event
            print('frame.payloadSize(Bytes)     {:#}'.format(size))
            print('eventFrame.FormatVersion     {:#}'.format(eventFrame.FormatVersion))
            print('eventFrame.PixReadIteration  {:#}'.format(eventFrame.PixReadIteration))
            print('eventFrame.StartPix          {:#}'.format(eventFrame.StartPix))
            print('eventFrame.StopPix           {:#}'.format(eventFrame.StopPix))
            print('eventFrame.SeqCnt            {:#}'.format(eventFrame.SeqCnt))            
            for i in range(numPixValues):
                print('eventFrame.pixValue[{:#}].TotOverflow {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].TotOverflow))
                print('eventFrame.pixValue[{:#}].TotData     {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].TotData))
                print('eventFrame.pixValue[{:#}].ToaOverflow {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].ToaOverflow))
                print('eventFrame.pixValue[{:#}].ToaData     {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].ToaData))
                print('eventFrame.pixValue[{:#}].Hit         {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].Hit))
                print('eventFrame.pixValue[{:#}].Sof         {:#}'.format(eventFrame.pixValue[i].PixelIndex,eventFrame.pixValue[i].Sof))

#################################################################
# Class for Reading the Data from File
class MyFileReader(rogue.interfaces.stream.Slave):

    def __init__(self):
        rogue.interfaces.stream.Slave.__init__(self)
        self.HitData = []
        self.HitDataTOTf_vpa = []
        self.HitDataTOTf_tz = []
        self.HitDataTOTc_vpa = []
        self.HitDataTOTc_tz = []
        self.HitDataTOTc_int1_vpa = []
        self.HitDataTOTc_int1_tz = []
        self.HitDataTOTf_vpa_temp = 0
        self.HitDataTOTc_vpa_temp = 0
        self.HitDataTOTf_tz_temp = 0
        self.HitDataTOTc_tz_temp = 0
        self.HitDataTOTc_int1_vpa_temp = 0
        self.HitDataTOTc_int1_tz_temp = 0

    def _acceptFrame(self,frame):
        # Get the payload data
        p = bytearray(frame.getPayload())
        # Return the buffer index
        frame.read(p,0)
        # Check for a modulo of 32-bit word 
        if ((len(p) % 4) == 0):
            count = int(len(p)/4)
            # Combine the byte array into 32-bit word array
            hitWrd = np.frombuffer(p, dtype='uint32', count=count)
            # Loop through each 32-bit word
            for i in range(count):
                # Parse the 32-bit word
                dat = ParseDataWord(hitWrd[i])
                # Print the event if hit

                if (dat.Hit > 0) and (dat.ToaOverflow == 0):
                   
                    self.HitData.append(dat.ToaData)
                
                if (dat.Hit > 0) and (dat.TotData != 0x1fc):
    
                    self.HitDataTOTf_vpa_temp = ((dat.TotData >>  0) & 0x3) + dat.TotOverflow*math.pow(2,2)
                    self.HitDataTOTc_vpa_temp = (dat.TotData >>  2) & 0x7F
                    self.HitDataTOTc_int1_vpa_temp = (((dat.TotData >>  2) + 1) >> 1) & 0x3F
                    #if ((dat.TotData >>  2) & 0x1) == 1:
                    self.HitDataTOTf_vpa.append(self.HitDataTOTf_vpa_temp)
                    self.HitDataTOTc_vpa.append(self.HitDataTOTc_vpa_temp)
                    self.HitDataTOTc_int1_vpa.append(self.HitDataTOTc_int1_vpa_temp)

                if (dat.Hit > 0) and (dat.TotData != 0x1f8):

                    self.HitDataTOTf_tz_temp = ((dat.TotData >>  0) & 0x7) + dat.TotOverflow*math.pow(2,3)
                    self.HitDataTOTc_tz_temp = (dat.TotData >>  3) & 0x3F
                    self.HitDataTOTc_int1_tz_temp = (((dat.TotData >>  3) + 1) >> 1) & 0x1F
                    self.HitDataTOTf_tz.append(self.HitDataTOTf_tz_temp)                    
                    self.HitDataTOTc_tz.append(self.HitDataTOTc_tz_temp)
                    self.HitDataTOTc_int1_tz.append(self.HitDataTOTc_int1_tz_temp)
                   
#################################################################