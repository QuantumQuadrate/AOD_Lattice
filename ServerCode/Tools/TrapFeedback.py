from simple_pid import PID
import time
import threading
import urllib
import json


class TrapFeedback(object):

        def __init__(self, waveManager, peakTool):
            self.peakTool = peakTool
            self.waveManager = waveManager
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

        def initializePIDs(self, channel):
            currentAmplitudes = self.waveManager.getAmplitudes(channel)
            for i in range(len(currentAmplitudes)):
                self.PIDs += [PID(self.P, self.I, self.D, setpoint=1000, output_limits=(-10, 0))]
                self.PIDs[i].auto_mode = False
                self.PIDs[i].set_auto_mode(True, last_output=currentAmplitudes[i])

        def measureIntensities(self, channel):
            dataNames = ['xAmplitudes', 'yAmplitudes']
            url = "http://128.104.162.32/peakData"
            response = urllib.urlopen(url)
            data = json.loads(response.read())
            return data[dataNames[channel]]

        def iteratePID(self, channel):
            t = threading.currentThread()
            self.running = True
            while getattr(t, "run", True):
                self.updateAmplitudes(self.measureIntensities(channel))
                time.sleep(self.waitTime)
                if not self.running:
                    break

        def startFeedback(self, channel):
            self.feedback = threading.Thread(target=self.iteratePID, args=[channel])
            self.feedback.start()

        def stopFeedback(self):
            self.running = False
            self.feedback.join()
