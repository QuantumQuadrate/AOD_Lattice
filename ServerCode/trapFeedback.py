from PIL import Image
import requests
from io import BytesIO
import numpy as np
from simple_pid import PID
import json
import time
from scipy.signal import find_peaks
import argparse
import math


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


def func(x, *params):
    y = np.zeros_like(x)
    for i in range(1, len(params), 3):
        ctr = params[i]
        amp = params[i+1]
        wid = params[i+2]
        y = y + amp * np.exp(-((x - ctr)/wid)**2)
    y += params[0]
    return y


def updateAmplitudes(pids, amplitudes, waveformFile):
    with open(waveformFile) as read_file:
        data = json.load(read_file)
    read_file.close()
    for i in range(len(pids)):
        control = pids[i](amplitudes[i])
        for chan in range(len(data["Channels"])):
            data["Waves"][chan][i]["amplitude"] = control
        print str(amplitudes[i]) + " " + str(control)
    with open(waveformFile, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '))
    outfile.close()
    return "done"


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", default=(90, 100, 338, 110), type=tuple)
    parser.add_argument("-t", "--traps", default=1, type=int)
    parser.add_argument("-P", "--P", default=.00005, type=float)
    parser.add_argument("-I", "--I", default=0.00002, type=float)
    parser.add_argument("-D", "--D", default=0.000001, type=float)
    parser.add_argument("-f", "--waveformFile", default='Resources/waveformArguments.json', type=str)
    parser.add_argument("-c", "--cameraImageURL", default="http://10.141.230.220/html/cam_pic.php", type=str)
    parser.add_argument("-p", "--peakProminence", default=400, type=int)
    return parser.parse_args()


args = parse_args()
trapNum = int(args.traps)
pids = []
with open(args.waveformFile) as read_file:
    data = json.load(read_file)
read_file.close()
for i in range(trapNum):
    pids += [PID(args.P, args.I, args.D, setpoint=1000, output_limits=(0, 1))]
    print data["Waves"][0][i]["amplitude"]
    pids[i].auto_mode = False
    pids[i].set_auto_mode(True, last_output=data["Waves"][0][i]["amplitude"])
while True:
    response = requests.get(args.cameraImageURL)
    img = (Image.open(BytesIO(response.content))).crop(args.window)
    grayimg = rgb2gray(np.array(img))
    summedFunction = np.sum(grayimg, axis=0)
    peaks, properties = find_peaks(summedFunction, prominence=(args.peakProminence, None))
    amplitudes = summedFunction[peaks]
    updateAmplitudes(pids, amplitudes[::-1], args.waveformFile)
    time.sleep(.1)
