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

Configuration_LOAD_file = 'config/testBojan11.yml' # <= Path to the Configuration File to be Loaded

pixel_number = 3 # <= Pixel to be Tested

DataAcqusitionTOA = 1   # <= Enable TOA Data Acquisition (Delay Sweep)
#DelayRange = 251        # <= Range of Programmable Delay Sweep 
DelayRange_low = 0     # <= low end of Programmable Delay Sweep
DelayRange_high = 4095     # <= high end of Programmable Delay Sweep
DelayRange_step = 100     # <= step size Programmable Delay Sweep
#DelayRange = 11        # <= Range of Programmable Delay Sweep 
NofIterationsTOA = 16  # <= Number of Iterations for each Delay value

DataAcqusitionTOT = 0   # <= Enable TOT Data Acquisition (Pulser Sweep)
PulserRangeL = 0        # <= Low Value of Pulser Sweep Range
PulserRangeH = 64       # <= High Value of Pulser Sweep Range
PulserRangeStep = 1     # <= Step Size of Pulser Sweep Range
NofIterationsTOT = 100   # <= Number of Iterations for each Pulser Value
DelayValueTOT = 100       # <= Value of Programmable Delay for TOT Pulser Sweep

nTOA_TOT_Processing = 0 # <= Selects the Data to be Processed and Plotted (0 = TOA, 1 = TOT) 

TOT_f_Calibration_En = 0                                       	   # <= Enables Calculation of TOT Fine-Interpolation Calibration Data and Saves them
#TOT_f_Calibration_LOAD_file = 'TestData/TOT_fine_nocalibration.txt'
TOT_f_Calibration_LOAD_file = 'TestData/TOT_fine_calibration2.txt'  # <= Path to the TOT Fine-Interpolation Calibration File used in TOT Data Processing
TOT_f_Calibration_SAVE_file = 'TestData/TOT_fine_calibration2.txt'  # <= Path to the File where TOT Fine-Interpolation Calibration Data are Saved

DelayStep = 9.27  # <= Estimate of the Programmable Delay Step in ps
LSB_TOTc = 190    # <= Estimate of TOT coarse LSB in ps
LSB_TOTc = 160
#LSB_TOTc = 1

nVPA_TZ = 0 # <= TOT TDC Processing Selection (0 = VPA TOT, 1 = TZ TOT) (!) Warning: TZ TOT not yet tested

HistDelayTOA1 = 100  # <= Delay Value for Histogram to be plotted in Plot (1,0)
HistDelayTOA2 = 200   # <= Delay Value for Histogram to be plotted in Plot (1,1)
HistPulserTOT1 = 32  # <= Pulser Value for Histogram to be plotted in Plot (1,0)
HistPulserTOT2 = 25  # <= Pulser Value for Histogram to be plotted in Plot (1,1)

Disable_CustomConfig = 0 # <= Disables the ASIC Configuration Customization inside the Script (Section Below) => all Configuration Parameters are taken from Configuration File   

TOTf_hist = 0
TOTc_hist = 0
Plot_TOTf_lin = 1
PlotValidCnt = 0

##############################################################################

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
                                                               ##
#################################################################


def set_fpga_for_custom_config(top):
    for i in range(25):
        top.Fpga[0].Asic.SlowControl.disable_pa[i].set(0x1)
        top.Fpga[0].Asic.SlowControl.ON_discri[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.EN_ck_SRAM[i].set(0x1)
        top.Fpga[0].Asic.SlowControl.EN_trig_ext[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.ON_Ctest[i].set(0x0)

        top.Fpga[0].Asic.SlowControl.cBit_f_TOA[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.cBit_s_TOA[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.cBit_f_TOT[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.cBit_s_TOT[i].set(0x0)
        top.Fpga[0].Asic.SlowControl.cBit_c_TOT[i].set(0x0)

    for i in range(16):
        top.Fpga[0].Asic.SlowControl.EN_trig_ext[i].set(0x0)

    top.Fpga[0].Asic.SlowControl.disable_pa[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.ON_discri[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.EN_hyst[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.EN_trig_ext[pixel_number].set(0x0)
    top.Fpga[0].Asic.SlowControl.EN_ck_SRAM[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.ON_Ctest[pixel_number].set(0x1)
    top.Fpga[0].Asic.SlowControl.bit_vth_cor[pixel_number].set(0x40)

    top.Fpga[0].Asic.SlowControl.Write_opt.set(0x0)
    top.Fpga[0].Asic.SlowControl.Precharge_opt.set(0x0)

    top.Fpga[0].Asic.SlowControl.DLL_ALockR_en.set(0x1)
    top.Fpga[0].Asic.SlowControl.CP_b.set(0x7) #5
    top.Fpga[0].Asic.SlowControl.ext_Vcrtlf_en.set(0x0) #0
    top.Fpga[0].Asic.SlowControl.ext_Vcrtls_en.set(0x1) #1
    top.Fpga[0].Asic.SlowControl.ext_Vcrtlc_en.set(0x0) #0

    top.Fpga[0].Asic.SlowControl.totf_satovfw.set(0x1)
    top.Fpga[0].Asic.SlowControl.totc_satovfw.set(0x1)
    top.Fpga[0].Asic.SlowControl.toa_satovfw.set(0x1)

    top.Fpga[0].Asic.SlowControl.SatFVa.set(0x3)
    top.Fpga[0].Asic.SlowControl.IntFVa.set(0x1)
    top.Fpga[0].Asic.SlowControl.SatFTz.set(0x4)
    top.Fpga[0].Asic.SlowControl.IntFTz.set(0x1)
    
    top.Fpga[0].Asic.SlowControl.cBitf.set(0xf) #0
    top.Fpga[0].Asic.SlowControl.cBits.set(0x0) #f
    top.Fpga[0].Asic.SlowControl.cBitc.set(0xf) #f

    top.Fpga[0].Asic.SlowControl.cBit_f_TOA[pixel_number].set(0x0)  #0
    top.Fpga[0].Asic.SlowControl.cBit_s_TOA[pixel_number].set(0xf)  #0
    top.Fpga[0].Asic.SlowControl.cBit_f_TOT[pixel_number].set(0xf)  #f
    top.Fpga[0].Asic.SlowControl.cBit_s_TOT[pixel_number].set(0x0)  #0
    top.Fpga[0].Asic.SlowControl.cBit_c_TOT[pixel_number].set(0xf)  #f
    top.Fpga[0].Asic.SlowControl.Rin_Vpa.set(0x1) #0
    top.Fpga[0].Asic.SlowControl.cd[0].set(0x0) #6
    top.Fpga[0].Asic.SlowControl.dac_biaspa.set(0x10) #10
    top.Fpga[0].Asic.SlowControl.dac_pulser.set(0x7) #7
    top.Fpga[0].Asic.SlowControl.DAC10bit.set(0x19f) #173 / 183

    top.Fpga[0].Asic.Gpio.DlyCalPulseSet.set(0x0)   # Rising edge of EXT_TRIG or CMD_PULSE delay
    top.Fpga[0].Asic.Gpio.DlyCalPulseSet.set(0xfff) # Falling edge of EXT_TRIG (independent of CMD_PULSE)

    top.Fpga[0].Asic.Readout.StartPix.set(pixel_number)
    top.Fpga[0].Asic.Readout.LastPix.set(pixel_number)
#################################################################


def acquire_data(range_low, range_high, range_step, top, asic_pulser, file_prefix, n_iterations): 
    for i in range(range_low, range_high, range_step):
        print (file_prefix+'step = %d',i)
        asic_pulser.set(i)

        filename = 'TestData/'+file_prefix+'%d.dat' %i
        try: os.remove(filename)
        except OSError: pass
        top.dataWriter._writer.open(filename)

        for j in range(n_iterations):
            top.Fpga[0].Asic.Gpio.RSTB_TDC.set(0x0)
            top.Fpga[0].Asic.Gpio.RSTB_TDC.set(0x1)
            time.sleep(0.01)
            top.Fpga[0].Asic.CalPulse.Start()
            time.sleep(0.001)

        top.dataWriter._writer.close()
#################################################################


def get_sweep_index(sweep_value, sweep_low, sweep_high, sweep_step):
    if sweep_value < sweep_low or sweep_high < sweep_value:
        raise ValueError( 'Sweep value {} outside of sweep range [{}:{}]'.format(sweep_value, sweep_low, sweep_high) )
    if sweep_value % sweep_step != 0:
        raise ValueError( 'Sweep value {} is not a multiple of sweep step {}'.format(sweep_value, sweep_step) )
    return int ( (sweep_value - sweep_low) / sweep_step )
#################################################################


#################################################################
# Set the argument parser
parser = argparse.ArgumentParser()

HistDelayTOA1_index  = get_sweep_index(HistDelayTOA1 , DelayRange_low, DelayRange_high, DelayRange_step)
HistDelayTOA2_index  = get_sweep_index(HistDelayTOA2 , DelayRange_low, DelayRange_high, DelayRange_step)
HistPulserTOT1_index = get_sweep_index(HistPulserTOT1, PulserRangeL, PulserRangeH, PulserRangeStep)
HistPulserTOT2_index = get_sweep_index(HistPulserTOT2, PulserRangeL, PulserRangeH, PulserRangeStep)


# Convert str to bool
argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']

# Add arguments
parser.add_argument(
    "--ip", 
    nargs    ='+',
    required = True,
    help     = "List of IP addresses",
)  
# Get the arguments
args = parser.parse_args()

#################################################################
# Setup root class
top = feb.Top(ip= args.ip)    

# Load the default YAML file
print('Loading Configuration File...')
top.LoadConfig(arg='config/defaults.yml')

# ... then load the User YAML file
top.LoadConfig(arg = Configuration_LOAD_file)

# Tap the streaming data interface (same interface that writes to file)
dataStream = feb.MyEventReader()    
pyrogue.streamTap(top.dataStream[0], dataStream) # Assuming only 1 FPGA

# Custom Configuration
if Disable_CustomConfig == 0:
    set_fpga_for_custom_config(top)

# Data Acquisition for TOA and TOT
if DataAcqusitionTOA == 1:
    acquire_data(DelayRange_low, DelayRange_high, DelayRange_step, top,
            top.Fpga[0].Asic.Gpio.DlyCalPulseSet, 'TOA', NofIterationsTOA)

top.Fpga[0].Asic.Gpio.DlyCalPulseSet.set(DelayValueTOT)

if DataAcqusitionTOT == 1:
    acquire_data(PulserRangeL, PulserRangeH, PulserStep, top, 
            top.Fpga[0].Asic.SlowControl.dac_pulser, 'TOT', NofIterationsTOT)

#######################
# Data Processing TOA #
#######################

if nTOA_TOT_Processing == 0:

    Delay = []
    HitCnt = []
    DataMean = []
    DataStdev = []

    for delay_value in range(DelayRange_low, DelayRange_high, DelayRange_step):
        # Create the File reader streaming interface
        dataReader = rogue.utilities.fileio.StreamReader()
        time.sleep(0.01)
        # Create the Event reader streaming interface
        dataStream = feb.MyFileReader()
        time.sleep(0.01)
        # Connect the file reader to the event reader
        pr.streamConnect(dataReader, dataStream) 
        time.sleep(0.01)
        # Open the file
        dataReader.open('TestData/TOA%d.dat' %delay_value)
        time.sleep(0.01)
        # Close file once everything processed
        dataReader.closeWait()
        time.sleep(0.01)
    
        try:
            print('Processing Data for Delay = %d...' % delay_value)
        except OSError:
            pass  

        HitData = dataStream.HitData

        exec("%s = %r" % ('HitData%d' %delay_value, HitData))

        Delay.append(delay_value)

        HitCnt.append(len(HitData))
        if len(HitData) > 0:
            print(HitData)
            DataMean.append(np.mean(HitData, dtype=np.float64))
            DataStdev.append(math.sqrt(math.pow(np.std(HitData, dtype=np.float64),2)+1/12))

        else:
            DataMean.append(0)
            DataStdev.append(0)
  
    # Average Std. Dev. Calculation; Points with no data (i.e. Std.Dev.= 0) are ignored
    index = np.where(np.sort(DataStdev))
    MeanDataStdev = np.mean(np.sort(DataStdev)[index[0][0]:len(np.sort(DataStdev))]) #FIXME!!

    # LSB estimation based on "DelayStep" value
    index=np.where(DataMean)
    fit = np.polyfit(Delay[index[0][5]:index[0][-5]], DataMean[index[0][5]:index[0][-5]], 1)
    LSBest = DelayStep/abs(fit[0])

#################################################################
# TOT Fine Interpolator Calibration

if nTOA_TOT_Processing == 1 and TOT_f_Calibration_En == 1:
    # Create the File reader streaming interface
    dataReader = rogue.utilities.fileio.StreamReader()
    time.sleep(0.01)
    # Create the Event reader streaming interface
    dataStream = feb.MyFileReader()
    time.sleep(0.01)
    # Connect the file reader to the event reader
    pr.streamConnect(dataReader, dataStream) 
    time.sleep(0.01)

    for i in range(PulserRangeL, PulserRangeH):
        # Open the file
        dataReader.open('TestData/TOT%d.dat' %i)
        time.sleep(0.01)
        # Close file once everything processed
        dataReader.closeWait()
        time.sleep(0.01)
    
    if not nVPA_TZ:    
        HitDataTOTf_cumulative = dataStream.HitDataTOTf_vpa
    else:
        HitDataTOTf_cumulative = dataStream.HitDataTOTf_tz
    
    TOTf_bin_width = np.zeros(16)
    for i in range(16):
        TOTf_bin_width[i]=len(list(np.where(np.asarray(HitDataTOTf_cumulative)==i))[0])
    TOTf_bin_width = TOTf_bin_width/sum(TOTf_bin_width)

    TOTf_bin = np.zeros(18)
    for i in range(1,17):
        TOTf_bin[i]=len(list(np.where(np.asarray(HitDataTOTf_cumulative)==i-1))[0])

    index = np.where(np.sort(TOTf_bin))
    LSB_TOTf_mean = np.mean(np.sort(TOTf_bin)[index[0][0]:len(np.sort(TOTf_bin))])/sum(TOTf_bin)

    TOTf_bin = (TOTf_bin[1:18]/2 + np.cumsum(TOTf_bin)[0:17])/sum(TOTf_bin)
    TOTf_bin[16] = LSB_TOTf_mean

    try:
        print('TOT Fine Interpolator Bin-Widths:')
        print(TOTf_bin_width*2*LSB_TOTc)
        print('Average TOT LSB = %f ps' % (LSB_TOTf_mean*2*LSB_TOTc))
    except OSError:
        pass   

    np.savetxt(TOT_f_Calibration_SAVE_file,TOTf_bin)

#################################################################
# Data Processing TOT

if nTOA_TOT_Processing == 1:

    Pulser = []
    ValidTOTCnt = []
    DataMeanTOT = []
    DataStdevTOT = []
    HitDataTOTf_cumulative = []

    for i in range(PulserRangeL, PulserRangeH):
        # Create the File reader streaming interface
        dataReader = rogue.utilities.fileio.StreamReader()
        time.sleep(0.01)
        # Create the Event reader streaming interface
        dataStream = MyFileReader()
        time.sleep(0.01)
        # Connect the file reader to the event reader
        pr.streamConnect(dataReader, dataStream) 
        time.sleep(0.01)
        # Open the file
        dataReader.open('TestData/TOT%d.dat' %i)
        time.sleep(0.01)
        # Close file once everything processed
        dataReader.closeWait()
        time.sleep(0.01)
    
        try:
            print('Processing Data for Pulser = %d...' % i)
        except OSError:
            pass  

        if not nVPA_TZ:    
            HitDataTOTf = dataStream.HitDataTOTf_vpa
            HitDataTOTc = dataStream.HitDataTOTc_vpa
            HitDataTOTc_int1 = dataStream.HitDataTOTc_int1_vpa
            HitDataTOTf_cumulative = HitDataTOTf_cumulative + dataStream.HitDataTOTf_vpa
        else:
            HitDataTOTf = dataStream.HitDataTOTf_tz
            HitDataTOTc = dataStream.HitDataTOTc_tz
            HitDataTOTc_int1 = dataStream.HitDataTOTc_int1_tz
            HitDataTOTf_cumulative = HitDataTOTf_cumulative + dataStream.HitDataTOTf_tz
    
        Pulser.append(i)
    
        TOTf_bin = np.loadtxt(TOT_f_Calibration_LOAD_file) 
        LSB_TOTf_mean = TOTf_bin[16]*2*LSB_TOTc

        def calibration_correction(f,c):
            if f > 3 and c == 0:
                return 2
            else:
                if f == 0 and c == 1:
                    return -TOTf_bin[0]*2
                else:
                    return 0
        IntFVa = 1
        if IntFVa == 1:
            if len(HitDataTOTf) > 0:
                HitDataTOT = list((np.asarray(HitDataTOTc_int1)*2 + 1 - np.asarray(list(map(lambda x: TOTf_bin[x], np.asarray(HitDataTOTf, dtype=np.int))))*2)*LSB_TOTc)
            
                HitDataTOT = list(HitDataTOT + np.asarray(list(map(calibration_correction, HitDataTOTf, list(map(lambda x: x&1, np.asarray(HitDataTOTc))))))*LSB_TOTc)
            else:
                HitDataTOT = []    
        else:
            if len(HitDataTOTf) > 0:
                HitDataTOT = list((np.asarray(HitDataTOTc) + 1 - np.asarray(HitDataTOTf)/4)*LSB_TOTc)
            else:
                HitDataTOT = []  

        #HitDataTOT = HitDataTOTc

        exec("%s = %r" % ('HitDataTOT%d' %i, HitDataTOT))
        exec("%s = %r" % ('HitDataTOTf%d' %i, HitDataTOTf))
        exec("%s = %r" % ('HitDataTOTc%d' %i, HitDataTOTc))

        ValidTOTCnt.append(len(HitDataTOT))
        if len(HitDataTOT) > 0:        
            DataMeanTOT.append(np.mean(HitDataTOT, dtype=np.float64))
            DataStdevTOT.append(math.sqrt(math.pow(np.std(HitDataTOT, dtype=np.float64),2) + math.pow(LSB_TOTf_mean,2)/12))

        else:
            DataMeanTOT.append(0)
            DataStdevTOT.append(0)

    # Average Std. Dev. Calculation; Points with no data (i.e. Std.Dev.= 0) are ignored
    index = np.where(np.sort(DataStdevTOT))
    MeanDataStdevTOT = np.mean(np.sort(DataStdevTOT)[index[0][0]:len(np.sort(DataStdevTOT))])

#################################################################
# Print Data
if nTOA_TOT_Processing == 0:
    for delay_index, delay_value in enumerate(Delay):
        try:
            print('Delay = %d, HitCnt = %d, DataMean = %f LSB, DataStDev = %f LSB' % (delay_value, HitCnt[delay_index], DataMean[delay_index], DataStdev[delay_index]))
        except OSError:
            pass   
    try:
        print('Maximum Measured TOA = %f LSB' % np.max(DataMean))
        print('Mean Std Dev = %f LSB' % MeanDataStdev)
    except OSError:
        pass
    for delay_index, delay_value in enumerate(Delay):
        try:
            print('Delay = %d, HitCnt = %d, DataMean = %f ps, DataStDev = %f ps' % (delay_value, HitCnt[delay_index], DataMean[delay_index]*LSBest, DataStdev[delay_index]*LSBest))
        except OSError:
            pass
    try:
        print('Maximum Measured TOA = %f ps' % (np.max(DataMean)*LSBest))
        print('Mean Std Dev = %f ps' % (MeanDataStdev*LSBest))
        print('Average LSB estimate: %f ps' % LSBest)
    except OSError:
        pass
#################################################################

#################################################################
# Plot Data

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows = 2, ncols = 2, figsize=(16,7))

# LSBest = 1

if nTOA_TOT_Processing == 0:
    # Plot (0,0)
    ax1.plot(Delay, np.multiply(DataMean,LSBest))
    ax1.grid(True)
    ax1.set_title('TOA Measurment VS Programmable Delay Value', fontsize = 11)
    ax1.set_xlabel('Programmable Delay Value [step estimate = %f ps]' % DelayStep, fontsize = 10)
    ax1.set_ylabel('Mean Value [ps]', fontsize = 10)
    ax1.legend(['LSB estimate: %f ps' % LSBest],loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    ax1.set_xlim(xmin = np.min(Delay), xmax = np.max(Delay))
    ax1.set_ylim(ymin = 0, ymax = np.max(np.multiply(DataMean,LSBest))+100)
else:
    # Plot (0,0)
    ax1.plot(Pulser, DataMeanTOT)
    ax1.grid(True)
    ax1.set_title('TOT Measurment VS Injected Charge', fontsize = 11)
    ax1.set_xlabel('Pulser DAC Value', fontsize = 10)
    ax1.set_ylabel('Mean Value [ps]', fontsize = 10)
    ax1.set_xlim(xmin = np.min(Pulser), xmax = np.max(Pulser))
    ax1.set_ylim(ymin = 0, ymax = np.max(DataMeanTOT)*1.1)

if nTOA_TOT_Processing == 0:
    # Plot (0,1)
    ax2.scatter(Delay, np.multiply(DataStdev,LSBest))
    ax2.grid(True)
    ax2.set_title('TOA Jitter VS Programmable Delay Value', fontsize = 11)
    ax2.set_xlabel('Programmable Delay Value', fontsize = 10)
    ax2.set_ylabel('Std. Dev. [ps]', fontsize = 10)
    ax2.legend(['Average Std. Dev. = %f ps' % (MeanDataStdev*LSBest)], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    ax2.set_xlim(xmin = np.min(Delay), xmax = np.max(Delay))
    ax2.set_ylim(ymin = 0, ymax = np.max(np.multiply(DataStdev,LSBest))+20)
else:
    # Plot (0,1)
    if PlotValidCnt == 0:
        ax2.scatter(Pulser, DataStdevTOT)
        ax2.grid(True)
        ax2.set_title('TOT Jitter VS Injected Charge', fontsize = 11)
        ax2.set_xlabel('Pulser DAC Value', fontsize = 10)
        ax2.set_ylabel('Std. Dev. [ps]', fontsize = 10)
        ax2.legend(['Average Std. Dev. = %f ps' % MeanDataStdevTOT], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
        ax2.set_xlim(xmin = np.min(Pulser), xmax = np.max(Pulser))
        ax2.set_ylim(ymin = 0, ymax = np.max(DataStdevTOT)*1.1)
    else:
        ax2.plot(Pulser, ValidTOTCnt)
        ax2.grid(True)
        ax2.set_title('TOT Valid Counts VS Injected Charge', fontsize = 11)
        ax2.set_xlabel('Pulser DAC Value', fontsize = 10)
        ax2.set_ylabel('Valid Measurements', fontsize = 10)
        ax2.set_xlim(xmin = np.min(Pulser), xmax = np.max(Pulser))
        ax2.set_ylim(ymin = 0, ymax = np.max(ValidTOTCnt)*1.1)

if nTOA_TOT_Processing == 0:
    # Plot (1,0)
    exec("DataL = len(HitData%d)" % HistDelayTOA1)
    if DataL:
        exec("ax3.hist(np.multiply(HitData%d,LSBest), bins = np.multiply(Delay,LSBest), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistDelayTOA1)
        exec("ax3.set_xlim(xmin = np.min(np.multiply(HitData%d,LSBest))-4*LSBest, xmax = np.max(np.multiply(HitData%d,LSBest))+4*LSBest)" % (HistDelayTOA1, HistDelayTOA1))
        ax3.set_title('TOA Measurment for Programmable Delay = %d' % HistDelayTOA1, fontsize = 11)
        ax3.set_xlabel('TOA Measurement [ps]', fontsize = 10)
        ax3.set_ylabel('N of Measrements', fontsize = 10)
        ax3.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMean[HistDelayTOA1_index]*LSBest, DataStdev[HistDelayTOA1_index]*LSBest, HitCnt[HistDelayTOA1_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
else:
    # Plot (1,0)
    #exec("print(HitDataTOT%d)" % HistPulserTOT1)
    #exec("print(HitDataTOTf%d)" % HistPulserTOT1)
    #exec("print(HitDataTOTc%d)" % HistPulserTOT1)
    #exec("print(np.asarray(list(map(lambda x: TOTf_bin[x], np.asarray(HitDataTOTf%d, dtype=np.int))))*2)" % HistPulserTOT1)
    #exec("print(list(map(lambda x: x&1, np.asarray(HitDataTOTc%d))))" % HistPulserTOT1)
    if TOTf_hist == 0 and TOTc_hist == 0:
        exec("DataL = len(HitDataTOT%d)" % HistPulserTOT1)
        if DataL:
            exec("ax3.hist(HitDataTOT%d, bins = np.multiply(np.arange(512),LSB_TOTf_mean), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistPulserTOT1)
            exec("ax3.set_xlim(xmin = np.min(HitDataTOT%d)-10*LSB_TOTf_mean, xmax = np.max(HitDataTOT%d)+10*LSB_TOTf_mean)" % (HistPulserTOT1, HistPulserTOT1))
            ax3.set_title('TOT Measurment for Pulser = %d' % HistPulserTOT1, fontsize = 11)
            ax3.set_xlabel('TOT Measurement [ps]', fontsize = 10)
            ax3.set_ylabel('N of Measrements', fontsize = 10)
            ax3.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMeanTOT[HistPulserTOT1_index], DataStdevTOT[HistPulserTOT1_index], ValidTOTCnt[HistPulserTOT1_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    else:
        if TOTf_hist == 1:
            exec("ax3.hist(HitDataTOTf%d, bins = np.arange(9), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistPulserTOT1)
            ax3.set_xlim(xmin = -1, xmax = 8)
            ax3.set_title('TOT Measurment for Pulser = %d' % HistPulserTOT1, fontsize = 11)
            ax3.set_xlabel('TOT Measurement [ps]', fontsize = 10)
            ax3.set_ylabel('N of Measrements', fontsize = 10)
            ax3.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMeanTOT[HistPulserTOT1_index], DataStdevTOT[HistPulserTOT1_index], ValidTOTCnt[HistPulserTOT1_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
        else: 
            if TOTc_hist == 1:
                exec("ax3.hist(HitDataTOTc%d, bins = np.arange(129), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistPulserTOT1)
                ax3.set_xlim(xmin = -1, xmax = 128)
                ax3.set_title('TOT Measurment for Pulser = %d' % HistPulserTOT1, fontsize = 11)
                ax3.set_xlabel('TOT Measurement [ps]', fontsize = 10)
                ax3.set_ylabel('N of Measrements', fontsize = 10)
                ax3.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMeanTOT[HistPulserTOT1_index], DataStdevTOT[HistPulserTOT1_index], ValidTOTCnt[HistPulserTOT1_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)

if nTOA_TOT_Processing == 0:
    # Plot (1,1)
    if PlotValidCnt == 0:
        exec("DataL = len(HitData%d)" % HistDelayTOA2)
        if DataL:
            exec("ax4.hist(np.multiply(HitData%d,LSBest), bins = np.multiply(Delay,LSBest), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistDelayTOA2)
            exec("ax4.set_xlim(xmin = np.min(np.multiply(HitData%d,LSBest))-10*LSBest, xmax = np.max(np.multiply(HitData%d,LSBest))+10*LSBest)" % (HistDelayTOA2, HistDelayTOA2))
            ax4.set_title('TOA Measurment for Programmable Delay = %d' % HistDelayTOA2, fontsize = 11)
            ax4.set_xlabel('TOA Measurement [ps]', fontsize = 10)
            ax4.set_ylabel('N of Measrements', fontsize = 10)
            ax4.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMean[HistDelayTOA2_index]*LSBest, DataStdev[HistDelayTOA2_index]*LSBest, HitCnt[HistDelayTOA2_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    else:
        ax4.plot(Delay, HitCnt)
        ax4.grid(True)
        ax4.set_title('TOA Valid Counts VS Injected Charge', fontsize = 11)
        ax4.set_xlabel('Programmable Delay Value', fontsize = 10)
        ax4.set_ylabel('Valid Measurements', fontsize = 10)
        ax4.set_xlim(xmin = np.min(Delay), xmax = np.max(Delay))
        ax4.set_ylim(ymin = 0, ymax = np.max(HitCnt)*1.1)
else:
    # Plot (1,1)
    if Plot_TOTf_lin == 0:
        exec("DataL = len(HitDataTOT%d)" % HistPulserTOT2)
        if DataL:
            exec("ax4.hist(HitDataTOT%d, bins = np.multiply(np.arange(512),LSB_TOTf_mean), align = 'left', edgecolor = 'k', color = 'royalblue')" % HistPulserTOT2)
            exec("ax4.set_xlim(xmin = np.min(HitDataTOT%d)-4*LSB_TOTf_mean, xmax = np.max(HitDataTOT%d)+4*LSB_TOTf_mean)" % (HistPulserTOT2, HistPulserTOT2))
            ax4.set_title('TOT Measurment for Pulser = %d' % HistPulserTOT2, fontsize = 11)
            ax4.set_xlabel('TOT Measurement [ps]', fontsize = 10)
            ax4.set_ylabel('N of Measrements', fontsize = 10)
            ax4.legend(['Mean = %f ps \nStd. Dev. = %f ps \nN of Events = %d' % (DataMeanTOT[HistPulserTOT2_index], DataStdevTOT[HistPulserTOT2_index], ValidTOTCnt[HistPulserTOT2_index])], loc = 'upper right', fontsize = 9, markerfirst = False, markerscale = 0, handlelength = 0)
    else:
        ax4.hist(HitDataTOTf_cumulative, bins = np.arange(9), edgecolor = 'k', color = 'royalblue')
        ax4.set_xlim(xmin = -1, xmax = 8)
        ax4.grid(True)
        ax4.set_title('TOT Fine Interpolation Linearity', fontsize = 11)
        ax4.set_xlabel('TOT Fine Code', fontsize = 10)
        ax4.set_ylabel('N of Measrements', fontsize = 10)

plt.subplots_adjust(hspace = 0.35, wspace = 0.2)
plt.show()
#################################################################

time.sleep(0.5)
# Close
top.stop()
