
import numpy as np
from simple_pid import PID
import json
import time
from scipy.signal import find_peaks
import argparse
from Tools.BlackFlyClient import BlackFlyClient
from scipy import ndimage
import math


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--area", default=[(109, 106), (193, 192)], type=list)
    parser.add_argument("-r", "--rotation", default=43, type=int)
    parser.add_argument("-P", "--P", default=.00005, type=float)
    parser.add_argument("-I", "--I", default=0.00002, type=float)
    parser.add_argument("-D", "--D", default=0.000001, type=float)
    parser.add_argument("-f", "--waveformFile", default='Resources/waveformArguments.json', type=str)
    parser.add_argument("-c", "--cameraSerial", default=14353509, type=str)
    parser.add_argument("-p", "--peakProminence", default=400, type=int)
    parser.add_argument("-ch", "--channel", default=0, type=int)
    parser.add_argument("-s", "--serverIP", default="10.140.178.187", type=str)
    parser.add_argument("-x", "--xCut", default=10, type=int)
    parser.add_argument("-y", "--yCut", default=10, type=int)

    return parser.parse_args()


def updateAmplitudes(pids, amplitudes, waveformFile, channel):
    with open(waveformFile) as read_file:
        data = json.load(read_file)
    read_file.close()
    for i in range(len(pids)):
        control = pids[i](amplitudes[i])
        data["Waves"][channel][i]["amplitude"] = 10.0**(control/10.0)
        print str(amplitudes[i]) + " " + str(control)
    with open(waveformFile, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '))
    outfile.close()
    return "done"


def getTotalPower(data, channel):
    # power out of SDR with 4db attenuator and 0 gain with waveforms at 1
    zeroPower = -20
    amplifier = 34
    sumOfWaveforms = 0
    for i in range(len(data["Waves"][channel])):
        sumOfWaveforms += data["Waves"][channel][i]["amplitude"]
        print sumOfWaveforms
    return zeroPower+amplifier+10*math.log10(sumOfWaveforms)+data['Gain']


args = parse_args()

with open(args.waveformFile) as read_file:
    data = json.load(read_file)
read_file.close()
print getTotalPower(data, args.channel)

serverIP = args.serverIP
cameraSerial = args.cameraSerial
camera = BlackFlyClient(cameraSerial, serverIP)

left = 312
right = 612
top = 218
bottom = 522

cutSizeX = args.xCut
cutSizeY = args.yCut


trapNum = int(len(data["Waves"][args.channel]))
pids = []

for i in range(trapNum):
    pids += [PID(args.P, args.I, args.D, setpoint=1000, output_limits=(-10, 0))]
    print data["Waves"][args.channel][i]["amplitude"]
    pids[i].auto_mode = False
    pids[i].set_auto_mode(True, last_output=(10*math.log10(data["Waves"][args.channel][i]["amplitude"])))

while True:
    print getTotalPower(data, args.channel)
    grayimg = camera.getImage()
    grayimg = ndimage.rotate(grayimg, args.rotation)
    grayimg = grayimg[left:right, top:bottom]
    dim = grayimg.shape
    x0 = int(dim[0]/2)
    x1 = int(dim[0]/2)+cutSizeX
    y0 = int(dim[1]/2)
    y1 = int(dim[1]/2)+cutSizeY
    summedFunctionx = np.sum(grayimg[:][y0:y1], axis=0)
    summedFunctiony = np.sum(grayimg[x0:x1][:], axis=0)

    peaksx, properties = find_peaks(summedFunctionx, prominence=(args.peakProminence, None))
    peaksy, properties = find_peaks(summedFunctiony, prominence=(args.peakProminence, None))

    amplitudesx = summedFunctionx[peaksx]
    amplitudesy = summedFunctiony[peaksy]
    updateAmplitudes(pids, amplitudesx, args.waveformFile, args.channel)
    time.sleep(.05)
