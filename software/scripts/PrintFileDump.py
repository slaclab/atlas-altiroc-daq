#!/usr/bin/env python3
##############################################################################
## This file is part of 'ATLAS ALTIROC DEV'.
## It is subject to the license terms in the LICENSE.txt file found in the 
## top-level directory of this distribution and at: 
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
## No part of 'ATLAS ALTIROC DEV', including this file, 
## may be copied, modified, propagated, or distributed except according to 
## the terms contained in the LICENSE.txt file.
##############################################################################

import pyrogue as pr
import rogue.utilities.fileio
import numpy as np

import common as feb

import argparse
import sys
import os

#################################################################

class MyEventReader(rogue.interfaces.stream.Slave):

    def __init__(self):
        rogue.interfaces.stream.Slave.__init__(self)

    def _acceptFrame(self,frame):
        # Get the payload data
        p = bytearray(frame.getPayload())
        # Return the buffer index
        frame.read(p,0)
        # Check for a 32-bit word
        if len(p) == 4:
            # Combine the byte array into single 32-bit word
            hitWrd = np.frombuffer(p, dtype='uint32', count=1)
            # Parse the 32-bit word
            dat = feb.ParseDataWord(hitWrd[0])
            # Print the event
            print( 'Event[SeqCnt=0x%x]: (TotOverflow = %r, TotData = 0x%x), (ToaOverflow = %r, ToaData = 0x%x), hit=%r' % (
                    dat.SeqCnt,
                    dat.TotOverflow,
                    dat.TotData,
                    dat.ToaOverflow,
                    dat.ToaData,
                    dat.Hit,
            ))            

#################################################################

# Set the argument parser
parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument(
    "--dataFile", 
    type     = str,
    required = True,
    help     = "path to data file",
) 

# Get the arguments
args = parser.parse_args()

#################################################################

# Create the File reader streaming interface
dataReader = rogue.utilities.fileio.StreamReader()

# Create the Event reader streaming interface
dataStream = MyEventReader()

# Connect the file reader to the event reader
pr.streamConnect(dataReader, dataStream) 

# Open the file
dataReader.open(args.dataFile)

# Close file once everything processed
dataReader.closeWait()
