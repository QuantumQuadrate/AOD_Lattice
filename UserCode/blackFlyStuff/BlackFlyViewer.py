import zmq
import json
import time
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from scipy import ndimage


def addCamera(cameraSerial, socket):
    cmd = {
        'action': 'ADD_CAMERA',
        'serial': cameraSerial
    }
    socket.send(json.dumps(cmd))
    resp = json.loads(socket.recv())
    print "status: " + str(resp["status"])
    print "server message: " + resp["message"]

    if resp["status"] == 0:
        cmd = {
            'action': 'START',
            'serial': cameraSerial
        }
        socket.send(json.dumps(cmd))
        resp = json.loads(socket.recv())
        print resp
        print "status: " + str(resp["status"])
        print "server message: " + resp["message"]


def addCameraWithArea(cameraSerial, socket):
    cmd = {
        'action': 'ADD_CAMERA',
        'serial': cameraSerial,
        'area': [[104, 4], [704, 604]]
    }
    socket.send(json.dumps(cmd))
    resp = json.loads(socket.recv())
    print "status: " + str(resp["status"])
    print "server message: " + resp["message"]
    status = 1
    while status == 1:
            cmd = {
                'action': 'START',
                'serial': cameraSerial
            }
            socket.send(json.dumps(cmd))
            resp = json.loads(socket.recv())
            print resp
            print "status: " + str(resp["status"])
            status = resp["status"]
            print "server message: " + resp["message"]


app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget()
win.show()  ## show widget alone in its own window
win.setWindowTitle('Pointgrey Monitor by BG')
view = win.addViewBox()
view.setAspectLocked(True) # lock the aspect ratio so pixels are always square
img = pg.ImageItem()
view.addItem(img)
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 5000)
addr = "{}://{}:{}".format("tcp", "10.140.178.187", 55555)
print addr
socket.connect(addr)

cameraSerial = 14353502
addCameraWithArea(cameraSerial, socket)
imageNum = 0
interval = 100
percentile = 99.5


def updateData():

    try:
        starttime = time.time()
        cmd = {
            'action': 'GET_IMAGE',
            'serial': cameraSerial
        }
        socket.send(json.dumps(cmd))
        resp = json.loads(socket.recv())
        print "status: " + str(resp["status"])
        print "server message: " + resp["message"]
        image = np.array(resp["image"])
        rotation = 0
        grayimg = ndimage.rotate(image, rotation)
        print grayimg.shape
        img.setImage(grayimg)

        latency = int(1000 * (time.time() - starttime))
        print "latency: " + str(latency)
        QtCore.QTimer.singleShot(interval, updateData)
    except:
        QtCore.QTimer.singleShot(interval, updateData)


updateData()

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
