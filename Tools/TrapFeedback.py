from simple_pid import PID
import time
import threading
import urllib
import json
import ast
import math


class TrapFeedback(object):

        def __init__(self, waveManager):
            self.waveManager = waveManager
            self.PIDs = []
            self.P = .0005
            self.I = .000002
            self.D = .000001
            self.setpoint = 1000
            self.waitTime = .1

        def updateAmplitudes(self, measuredIntensities, channel):
            newAmplitudes = []
            print "updating"
            for i in range(len(self.PIDs)):
                newPower = self.PIDs[i](measuredIntensities[i])
                newAmplitudes += [10.0**(newPower/10.0)]
                print str(newPower) + " " + str(measuredIntensities[i])
            self.waveManager.changeAmplitudes(channel, newAmplitudes)
            self.waveManager.saveJsonData()

        def initializePIDs(self, channel):
            self.PIDs = []
            currentAmplitudes = self.waveManager.getAmplitudes(channel)
            print len(currentAmplitudes)
            for i in range(len(currentAmplitudes)):
                self.PIDs += [PID(self.P, self.I, self.D, setpoint=self.setpoint, output_limits=(-20, 0))]
                self.PIDs[i].auto_mode = False
                self.PIDs[i].set_auto_mode(True, last_output=10*math.log10(currentAmplitudes[i]))

        def measureIntensities(self, channel):
            dataNames = ['yAmplitudes', 'xAmplitudes']
            url = "http://128.104.162.32/peakData"
            response = urllib.urlopen(url)
            data = ast.literal_eval(response.read())
            return data[dataNames[channel]]

        def iteratePID(self, channel):
            t = threading.currentThread()
            self.running = True
            while getattr(t, "run", True):
                self.updateAmplitudes(self.measureIntensities(channel), channel)
                time.sleep(self.waitTime)
                if not self.running:
                    break

        def startFeedback(self, channel):
            self.feedback = threading.Thread(target=self.iteratePID, args=[channel])
            self.feedback.start()

        def stopFeedback(self):
            self.running = False
            self.feedback.join()
