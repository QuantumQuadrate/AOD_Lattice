from Tools.WaveformManager import WaveformManager
from Tools.TrapFeedback import TrapFeedback
from Tools.Servers import SDRServer

waveManager = WaveformManager("Resources/waveformArguments.json")
trapFeedback = TrapFeedback(waveManager)
Server = SDRServer()
Server.runServer(waveManager, trapFeedback)
