
import numpy as np
from simple_pid import PID
import json
import time
from scipy.signal import find_peaks
import argparse
import zmq
from scipy import ndimage


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", default=(98, 100, 324, 110), type=tuple)
    parser.add_argument("-t", "--traps", default=1, type=int)
    parser.add_argument("-P", "--P", default=.00005, type=float)
    parser.add_argument("-I", "--I", default=0.00002, type=float)
    parser.add_argument("-D", "--D", default=0.000001, type=float)
    parser.add_argument("-f", "--waveformFile", default='Resources/waveformArguments.json', type=str)
    parser.add_argument("-c", "--cameraImageURL", default="http://10.141.230.220/html/cam_pic.php", type=str)
    parser.add_argument("-p", "--peakProminence", default=400, type=int)
    return parser.parse_args()


def getImage(cameraSerial, socket):
    cmd = {
        'action': 'GET_IMAGE',
        'serial': cameraSerial
    }
    socket.send(json.dumps(cmd))
    resp = json.loads(socket.recv())
    print "status: " + str(resp["status"])
    print "server message: " + resp["message"]
    return np.array(resp["image"])


def addCamera():
    cmd = {
        'action': 'ADD_CAMERA',
        'serial': cameraSerial
    }
    socket.send(json.dumps(cmd))
    resp = json.loads(socket.recv())
    print "status: " + str(resp["status"])
    print "server message: " + resp["message"]

    cmd = {
        'action': 'START',
        'serial': cameraSerial
    }
    socket.send(json.dumps(cmd))
    resp = json.loads(socket.recv())
    print resp
    print "status: " + str(resp["status"])
    print "server message: " + resp["message"]


def updateAmplitudes(pids, amplitudes, waveformFile):
    with open(waveformFile) as read_file:
        data = json.load(read_file)
    read_file.close()
    for i in range(len(pids)):
        control = pids[i](amplitudes[i])
        for chan in range(len(data["Channels"])):
            data["Waves"][chan][i]["amplitude"] = 10.0**(control/10.0)
        print str(amplitudes[i]) + " " + str(control)
    with open(waveformFile, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '))
    outfile.close()
    return "done"


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 5000)
addr = "{}://{}:{}".format("tcp", "10.140.178.187", 55555)
socket.connect(addr)

cameraSerial = 14353509

args = parse_args()
trapNum = int(args.traps)
pids = []
rotation = 40
camArea = [(109, 106), (193, 192)]
cropArea = [(109, 106), (193, 192)]

with open(args.waveformFile) as read_file:
    data = json.load(read_file)
read_file.close()
for i in range(trapNum):
    pids += [PID(args.P, args.I, args.D, setpoint=1000, output_limits=(-10, 0))]
    print data["Waves"][0][i]["amplitude"]
    pids[i].auto_mode = False
    pids[i].set_auto_mode(True, last_output=data["Waves"][0][i]["amplitude"])

while True:
    grayimg = getImage(cameraSerial, socket)
    grayimg = ndimage.rotate(grayimg, rotation)
    grayimg = grayimg[cropArea[0][0]:cropArea[1][0], cropArea[0][1]:cropArea[1][1]]
    grayimg = np.transpose(grayimg)
    summedFunction = np.sum(grayimg, axis=0)
    peaks, properties = find_peaks(summedFunction, prominence=(args.peakProminence, None))
    amplitudes = summedFunction[peaks]
    updateAmplitudes(pids, amplitudes, args.waveformFile)
    time.sleep(.05)
