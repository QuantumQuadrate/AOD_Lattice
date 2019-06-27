from Tools.WaveformManager import WaveformManager
from Tools.TrapFeedback import TrapFeedback
from Server import Server

cameraSerial = 14353509
waveManager = WaveformManager("Resources/waveformArguments.json")
peakTool = []
trapFeedback = TrapFeedback(waveManager)
Server = Server()
Server.runServer(waveManager, peakTool, trapFeedback)
