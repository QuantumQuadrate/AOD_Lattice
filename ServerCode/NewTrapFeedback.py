from Tools.WaveformManager import WaveformManager
from Tools.TrapFeedback import TrapFeedback
from Tools.BlackFlyClient import BlackFlyClient
import numpy as np


def turnChannelOff(channel, waveManager):
    waveManager.changeAmplitudes(channel, np.zeros(len(waveManager.getAmplitudes())))
    waveManager.saveJsonData()
cameraSerial = 14353509
cameraServerIP = "128.104.162.32"
camera = BlackFlyClient(cameraSerial, serverIP)
camera.addCamera()
waveManager = WaveformManager("Resources/waveformArguments.json")
trapFeedback0 = TrapFeedback(waveManager, 0, camera)
trapFeedback1 = TrapFeedback(waveManager, 1, camera)
