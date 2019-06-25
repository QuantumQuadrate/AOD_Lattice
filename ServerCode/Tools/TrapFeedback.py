import numpy as np
from simple_pid import PID
import time
from scipy.signal import find_peaks
import threading
from BlackFlyClient import BlackFlyClient


class TrapFeedback(object):

        def __init__(self, waveManager, channel, cameraSerial, serverIP):
            self.camera = BlackFlyClient(cameraSerial, serverIP)
            self.waveManager = waveManager
            self.channel = channel
            self.trapNum = len(waveManager.getAmplitudes(self.channel))
            self.PIDs = []
            self.P = .0005
            self.I = .00002
            self.D = .00001
            self.peakProminence = 200
            self.waitTime = 1
            self.initializePIDs()

        def updateAmplitudes(self, measuredIntensities):
            newAmplitudes = []
            for i in range(len(self.PIDs)):
                newPower = self.PIDs[i](measuredIntensities[i])
                newAmplitudes += [10.0**(newPower/10.0)]
            self.waveManager.changeAmplitude(self.channel, newAmplitudes)
            self.waveManager.saveJsonData()

        def initializePIDs(self):
            currentAmplitudes = self.waveManager.getAmplitudes(self.channel)
            for i in range(len(currentAmplitudes)):
                self.PIDs += [PID(self.P, self.I, self.D, setpoint=1000, output_limits=(-10, 0))]
                self.PIDs[i].auto_mode = False
                self.PIDs[i].set_auto_mode(True, last_output=currentAmplitudes[i])

        def measureIntensities(self):
            image = self.camera.getImage()
            summedFunction = np.sum(image, axis=0)
            peaks, properties = find_peaks(summedFunction, prominence=(self.peakProminence, None))
            return summedFunction[peaks]

        def iteratePID(self):
            t = threading.currentThread()
            self.running = True
            while getattr(t, "run", True):
                self.updateAmplitudes(self.measureIntensities())
                time.sleep(self.waitTime)
                if not self.running:
                    break

        def startFeedback(self):
            self.feedback = threading.Thread(target=self.iteratePID, args=[])
            self.feedback.start()

        def stopFeedback(self):
            self.running = False
            self.feedback.join()
