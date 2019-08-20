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

##############################################################################
# Script Settings

asicVersion = 1 # <= Select either V1 or V2 of the ASIC
DebugPrint = True
NofIterationsTOA = 16  # <= Number of Iterations for each Delay value
DelayStep = 9.5582  # <= Estimate of the Programmable Delay Step in ps (measured on 10JULY2019)

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
                                                               ##
import statistics                                              ##
import math                                                    ##
import matplotlib.pyplot as plt                                ##
from setASICconfig_v2B6 import *                               ##
#from setASICconfig_v2B7 import *                               ##
                                                               ##
#################################################################


def set_pixel_specific_parameters(top, pixel_number):
    if pixel_number in range(0, 5): bitset=0x1
    if pixel_number in range(5, 10): bitset=0x2
    if pixel_number in range(10, 15): bitset=0x4
    if pixel_number in range(15, 20): bitset=0x8
    if pixel_number in range(20, 25): bitset=0x10
    top.Fpga[0].Asic.Probe.en_probe_dig.set(bitset)
    top.Fpga[0].Asic.Probe.EN_dout.set(bitset)

    top.Fpga[0].Asic.Probe.pix[pixel_number].probe_pa.set(0x1)
    top.Fpga[0].Asic.Probe.pix[pixel_number].probe_vthc.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].probe_dig_out_disc.set(0x1)
    top.Fpga[0].Asic.Probe.pix[pixel_number].probe_toa.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].probe_tot.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].totf.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].tot_overflow.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].toa_busy.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].Hit.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].tot_busy.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].tot_ready.set(0x0)
    top.Fpga[0].Asic.Probe.pix[pixel_number].en_read.set(0x1)

    top.Fpga[0].Asic.SlowControl.disable_pa[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.ON_discri[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.EN_hyst[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.EN_trig_ext[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.EN_ck_SRAM[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.ON_Ctest[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.bit_vth_cor[pixel_number].set(0x40)

    top.Fpga[0].Asic.SlowControl.cBit_f_TOA[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.cBit_s_TOA[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.cBit_f_TOT[pixel_number].set(0xf)
    top.Fpga[0].Asic.SlowControl.cBit_s_TOT[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.cBit_c_TOT[pixel_number].set(0xf)
    
    top.Fpga[0].Asic.Readout.StartPix.set(pixel_number)
    top.Fpga[0].Asic.Readout.LastPix.set(pixel_number)


def acquire_data(top, DelayRange): 
    pixel_stream = feb.PixelReader()    
    pyrogue.streamTap(top.dataStream[0], pixel_stream) # Assuming only 1 FPGA
    pixelData = []

    for delay_value in DelayRange:
        print('Testing delay value ' + str(delay_value) )
        top.Fpga[0].Asic.Gpio.DlyCalPulseSet.set(delay_value)

        for pulse_iteration in range(NofIterationsTOA):
            if (asicVersion == 1):
                top.Fpga[0].Asic.LegacyV1AsicCalPulseStart()
                time.sleep(0.001)
            else:
                top.Fpga[0].Asic.CalPulse.Start()
                time.sleep(0.001)
        pixelData.append( pixel_stream.HitData.copy() )
        while pixel_stream.count < NofIterationsTOA: pass
        pixel_stream.clear()
    return pixelData
#################################################################


def parse_arguments():
    parser = argparse.ArgumentParser()
    
    # Convert str to bool
    argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']
    
    #default parameters
    pixel_number = 4
    DAC_Vth = 320
    Qinj = 13 #10fc
    config_file = 'config/measureTOA_B6.yml'
    dlyMin = 2300 
    dlyMax = 2700 
    dlyStep = 10
    
    
    # Add arguments
    parser.add_argument( "--ip", nargs ='+', required = True, help = "List of IP addresses",)  
    parser.add_argument("--cfg", type = str, required = False, default = config_file, help = "config file")
    parser.add_argument("--ch", type = int, required = False, default = pixel_number, help = "channel")
    parser.add_argument("--Q", type = int, required = False, default = Qinj, help = "injected charge DAC")
    parser.add_argument("--DAC", type = int, required = False, default = DAC_Vth, help = "DAC vth")
    parser.add_argument("--delayMin", type = int, required = False, default = dlyMin, help = "scan start")
    parser.add_argument("--delayMax", type = int, required = False, default = dlyMax, help = "scan stop")
    parser.add_argument("--delayStep", type = int, required = False, default = dlyStep, help = "scan step")

    # Get the arguments
    args = parser.parse_args()
    return args
#################################################################


def measureTOA(argsip,
      Configuration_LOAD_file,
      pixel_number,
      Qinj,
      DAC,
      delayMin,
      delayMax,
      delayStep):

    DelayRange = range( delayMin, delayMax, delayStep )
    
    # Setup root class
    top = feb.Top(ip = argsip)    
    
    # Load the YAML file
    print('Loading {Configuration_LOAD_file} Configuration File...')
    top.LoadConfig(arg = Configuration_LOAD_file)
    
    if DebugPrint:
        # Tap the streaming data interface (same interface that writes to file)
        dataStream = feb.PrintEventReader()    
        pyrogue.streamTap(top.dataStream[0], dataStream) # Assuming only 1 FPGA

    #testing resets
    top.Fpga[0].Asic.Gpio.RSTB_DLL.set(0x0) #NOTE be careful of these...
    time.sleep(0.001)
    top.Fpga[0].Asic.Gpio.RSTB_DLL.set(0x1)
    time.sleep(0.001)
    top.Fpga[0].Asic.Gpio.RSTB_TDC.set(0x0)
    time.sleep(0.001)
    top.Fpga[0].Asic.Gpio.RSTB_TDC.set(0x1)

    set_pixel_specific_parameters(top, pixel_number)
    
    # Custom Configuration
    #set_fpga_for_custom_config(top,pixel_number)
    top.Fpga[0].Asic.SlowControl.DAC10bit.set(DAC) #NOTE: be carefule of these...
    top.Fpga[0].Asic.SlowControl.dac_pulser.set(Qinj)

    
    # Data Acquisition for TOA
    pixel_data = acquire_data(top, DelayRange)
    
    #######################
    # Data Processing TOA #
    #######################
    
    if len(pixel_data) == 0: raise ValueError('No hits were detected during delay sweep. Aborting!')

    HitCnt = []
    DataMean = np.zeros(len(DelayRange))
    DataStdev = np.zeros(len(DelayRange))
    
    for delay_index, delay_value in enumerate(DelayRange):
        HitData = pixel_data[delay_index]
        HitCnt.append(len(HitData))
        if len(HitData) > 0:
            DataMean[delay_index] = np.mean(HitData, dtype=np.float64)
            DataStdev[delay_index] = math.sqrt(math.pow(np.std(HitData, dtype=np.float64),2)+1/12)
    
    # The following calculations ignore points with no data (i.e. Std.Dev = 0)
    nonzero = DataMean != 0
    
    # Average Std. Dev. Calculation; Points with no data (i.e. Std.Dev.= 0) are ignored
    MeanDataStdev = np.mean(DataStdev[nonzero])
    
    # LSB estimation based on "DelayStep" value, again ignoring zero values
    safety_bound = 2 #so we don't measure too close to the edges of the pulse 
    Delay = np.array(DelayRange)
    fit_x_values = Delay[nonzero][safety_bound:-safety_bound]
    fit_y_values = DataMean[nonzero][safety_bound:-safety_bound]
    if len(fit_x_values) == 0: 
        LSBest = 99999
        print('\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('WARNING! YOU HAVE TRIED TO FIT OVER TOO FEW VALUES!')
        print('LSB ESTIMATE CALCULATION IS BEING SKIPPED!')
        print('LSB ESTIMATE DEFAULTED TO ' + str(LSBest) )
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
    else:
        linear_fit_slope = np.polyfit(fit_x_values, fit_y_values, 1)[0]
        LSBest = DelayStep/abs(linear_fit_slope)
    
    
    #################################################################
    # Print Data
    for delay_index, delay_value in enumerate(DelayRange):
        print('Delay = %d, HitCnt = %d, DataMean = %f LSB, DataStDev = %f LSB / %f ps' % (delay_value, HitCnt[delay_index], DataMean[delay_index], DataStdev[delay_index], DataStdev[delay_index]*LSBest))
    print('Maximum Measured TOA = %f LSB / %f ps' % ( np.max(DataMean), (np.max(DataMean)*LSBest) ) )
    print('Mean Std Dev = %f LSB / %f ps' % ( MeanDataStdev, (MeanDataStdev*LSBest) ) )
    print('Average LSB estimate: %f ps' % LSBest)
    #################################################################
    
    #################################################################
    # Plot Data
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows = 2, ncols = 2, figsize=(16,7))
    
    # Plot (0,0) ; top left
    ax1.plot(Delay, DataMean)
    ax1.grid(True)
    ax1.set_title('TOA Measurment VS Programmable Delay Value', fontsize = 11)
    ax1.set_xlabel('Programmable Delay Value [step estimate = %f ps]' % DelayStep, fontsize = 10)
    ax1.set_ylabel('Mean Value [ps]', fontsize = 10)
    ax1.legend(['LSB estimate: %f ps' % LSBest],loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    ax1.set_xlim(left = np.min(Delay), right = np.max(Delay))
    #ax1.set_ylim(bottom = 0, top = np.max(np.multiply(DataMean,LSBest))+100)
    ax1.set_ylim(bottom = 0, top = np.max(DataMean)+10)
    
    # Plot (0,1) ; top right
    ax2.scatter(Delay, np.multiply(DataStdev,LSBest))
    ax2.grid(True)
    ax2.set_title('TOA Jitter VS Programmable Delay Value', fontsize = 11)
    ax2.set_xlabel('Programmable Delay Value', fontsize = 10)
    ax2.set_ylabel('Std. Dev. [ps]', fontsize = 10)
    ax2.legend(['Average Std. Dev. = %f ps' % (MeanDataStdev*LSBest)], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    ax2.set_xlim(left = np.min(Delay), right = np.max(Delay))
    ax2.set_ylim(bottom = 0, top = np.max(np.multiply(DataStdev,LSBest))+20)
    
    # Plot (1,0) ; bottom left
    
    delay_index_to_plot = -1
    for delay_index, delay_value in enumerate(DelayRange): #find a good delay value to plot
        #I'd say having 80% of hits come back is good enough to plot
        if HitCnt[delay_index] > NofIterationsTOA * 0.8:
            delay_index_to_plot = delay_index
            break
    
    if delay_index_to_plot != -1:
        hist_range = 10
        binlow = ( int(DataMean[delay_index_to_plot])-hist_range ) * LSBest
        binhigh = ( int(DataMean[delay_index_to_plot])+hist_range ) * LSBest
        hist_bin_list = np.arange(binlow, binhigh, LSBest)
        ax3.hist(np.multiply(pixel_data[delay_index_to_plot],LSBest), bins = hist_bin_list, align = 'left', edgecolor = 'k', color = 'royalblue')
        ax3.set_title('TOA Measurment for Programmable Delay = %d' % DelayRange[delay_index_to_plot], fontsize = 11)
        ax3.set_xlabel('TOA Measurement [ps]', fontsize = 10)
        ax3.set_ylabel('N of Measrements', fontsize = 10)
        ax3.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMean[delay_index_to_plot]*LSBest, DataStdev[delay_index_to_plot]*LSBest, HitCnt[delay_index_to_plot])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    
    # Plot (1,1)
    ax4.plot(Delay, HitCnt)
    ax4.grid(True)
    ax4.set_title('TOA Valid Counts VS Programmable Delay Value', fontsize = 11)
    ax4.set_xlabel('Programmable Delay Value', fontsize = 10)
    ax4.set_ylabel('Valid Measurements', fontsize = 10)
    ax4.set_xlim(left = np.min(Delay), right = np.max(Delay))
    ax4.set_ylim(bottom = 0, top = np.max(HitCnt)*1.1)
    
    plt.subplots_adjust(hspace = 0.35, wspace = 0.2)
    plt.show()
    #################################################################
    
    time.sleep(0.5)
    # Close
    top.stop()
    #################################################################




if __name__ == "__main__":
    args = parse_arguments()
    print(args)
    measureTOA(args.ip, args.cfg, args.ch, args.Q, args.DAC, args.delayMin, args.delayMax, args.delayStep)
