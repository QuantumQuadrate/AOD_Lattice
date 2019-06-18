from Tools.WaveformManager import WaveformManager
from Tools.SoftwareDefinedRadio import SoftwareDefinedRadio
from Tools.TrapFeedback import TrapFeedback


waveManager = WaveformManager("Resources/waveformArguments.json")
trapFeedback = TrapFeedback(waveManager, 0, 14353509, "128.104.162.32")

SDR = SoftwareDefinedRadio(waveMonitor)
SDR.initializeSDR()
SDR.startMonitor()
