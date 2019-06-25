from Tools.WaveformManager import WaveformManager
from Tools.TrapFeedback import TrapFeedback
import numpy as np


def turnChannelOff(channel, waveManager):
    waveManager.changeAmplitudes(channel, np.zeros(len(waveManager.getAmplitudes())))
    waveManager.saveJsonData()


waveManager = WaveformManager("Resources/waveformArguments.json")
trapFeedback0 = TrapFeedback(waveManager, 0, 14353509, "128.104.162.32")
trapFeedback1 = TrapFeedback(waveManager, 1, 14353509, "128.104.162.32")
