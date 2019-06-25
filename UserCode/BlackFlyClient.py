import zmq
import json
import numpy as np


class BlackFlyClient(object):

    def __init__(self, cameraSerial, serverIP, area=None):
        self.serverIP = serverIP
        self.cameraSerial = cameraSerial
        self.connectCameraServer()
        if area is None:
            self.addCamera()
        else:
            self.addCameraWithArea(area)

    def connectCameraServer(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        addr = "{}://{}:{}".format("tcp", self.serverIP, 55555)
        self.socket.connect(addr)

    def addCamera(self):
        cmd = {
            'action': 'ADD_CAMERA',
            'serial': self.cameraSerial
        }
        self.socket.send(json.dumps(cmd))
        resp = json.loads(self.socket.recv())
        print "status: " + str(resp["status"])
        print "server message: " + resp["message"]
        if resp["status"] == 0:
            cmd = {
                'action': 'START',
                'serial': self.cameraSerial
            }
            self.socket.send(json.dumps(cmd))
            resp = json.loads(self.socket.recv())
            print resp
            print "status: " + str(resp["status"])
            print "server message: " + resp["message"]

    def addCameraWithArea(self, area):
        cmd = {
            'action': 'ADD_CAMERA',
            'serial': self.cameraSerial,
            'area': area
        }
        self.socket.send(json.dumps(cmd))
        resp = json.loads(self.socket.recv())
        print "status: " + str(resp["status"])
        print "server message: " + resp["message"]
        if resp["status"] == 0:
            cmd = {
                'action': 'START',
                'serial': self.cameraSerial
            }
            self.socket.send(json.dumps(cmd))
            resp = json.loads(self.socket.recv())
            print resp
            print "status: " + str(resp["status"])
            print "server message: " + resp["message"]

    def getImage(self):
        cmd = {
            'action': 'GET_IMAGE',
            'serial': self.cameraSerial
        }
        self.socket.send(json.dumps(cmd))
        resp = json.loads(self.socket.recv())
        print "status: " + str(resp["status"])
        print "server message: " + resp["message"]
        return np.array(resp["image"])
