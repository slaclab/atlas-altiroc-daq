#!/usr/bin/env python3
#convert testbeam data into txt
#################################################################
                                                               ##
import sys                                                     ##
import rogue                                                   ##
import time                                                    ##
import random                                                  ##
import argparse                                                ##
                                                               ##
import pyrogue as pr                                           ##
import pyrogue.gui                                             ##
import numpy as np                                             ##
import common as feb                                           ##
                                                               ##
import os                                                      ##
import rogue.utilities.fileio                                  ##
#################################################################
def parse_arguments():
    parser = argparse.ArgumentParser()

    # Convert str to bool
    argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']
    
    parser.add_argument("--infile", nargs ='+',required = True, help = "input files")

    # Get the arguments
    args = parser.parse_args()
    return args
#################################################################

def convertTBdata(inFiles):
    for inFile in inFiles:
        print("Opening file "+inFile)

        # Create the File reader streaming interface
        dataReader = rogue.utilities.fileio.StreamReader()

        # Create the Event reader streaming interface
        dataStream = feb.BeamTestFileReader()

        # Connect the file reader ---> event reader
        pr.streamConnect(dataReader, dataStream)

        # Open the file
        dataReader.open(inFile)

        # Close file once everything processed
        dataReader.closeWait()

        HitDataTOA = dataStream.HitDataTOA
        HitDataTOTc = dataStream.HitDataTOTc_vpa
        HitDataTOTf = dataStream.HitDataTOTf_vpa
        overflowTOA = dataStream.TOAOvflow
        overflowTOT = dataStream.TOAOvflow
        pixelID = dataStream.pixelId  
        fpga_channel = dataStream.FPGA_channel
        seq_cnt_list = dataStream.SeqCnt
        trig_cnt_list = dataStream.TrigCnt

        cntTOA = len(HitDataTOA)
        cntTOT = len(HitDataTOTc)

        number_of_fpgas = 2
        output_text_data = ['']*number_of_fpgas

        for frame_index in range( len(HitDataTOA) ):
            if frame_index%100 == 0: 
                print(" reading out frame "+str(frame_index))
            fpga_index = fpga_channel[frame_index]
            seqcnt = seq_cnt_list[frame_index]
            trigcnt = trig_cnt_list[frame_index]
            
            #output_text_data[fpga_index] += 'frame {} {} {}\n'.format(frame_index,seqcnt,trigcnt)
            output_text_data[fpga_index] += 'frame {} \n'.format(frame_index)
            for channel in range( len(HitDataTOA[frame_index]) ):
                toa = HitDataTOA[frame_index][channel]
                totc = HitDataTOTc[frame_index][channel]
                totf = HitDataTOTf[frame_index][channel]
                toaOV = overflowTOA[frame_index][channel]
                totOV = overflowTOT[frame_index][channel]
                pixID = pixelID[frame_index][channel]
                output_text_data[fpga_index] += '{} {} {} {} {} {}\n'.format(pixID,toa,totc,totf,toaOV,totOV)
                #print('{} {} {} {} {} {}\n'.format(pixID,toa,totc,totf,toaOV,totOV))

        #name output equal to input
        for fpga_index in range(number_of_fpgas):
            outFile_base = inFile[:inFile.find('.dat')]+'_fpga'+str(fpga_index)
            if os.path.exists(outFile_base+'.txt'):
                ts = str(int(time.time()))
                outFile_base += '_' + ts
                print('File exists, will be saved as '+outFile_base+'.txt')
            outFile = outFile_base + '.txt'
            myfile = open(outFile,'w+')
            myfile.write(output_text_data[fpga_index])
            myfile.close()
    
#################################################################
if __name__ == "__main__":
    args = parse_arguments()
    print(args)    
    convertTBdata(args.infile)
