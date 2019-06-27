from Tools.WaveformMonitor import WaveformMonitor
from Tools.WaveformManager import WaveformManager
from Tools.peakAnalysisTools import peakAnalysisTools
from Tools.BlackflyCamera import BlackflyCamera
from Tools.TrapFeedback import TrapFeedback
from Server import Server

cameraSerial = 14353509
waveManager = WaveformManager("Resources/waveformArguments.json")
waveMonitor = WaveformMonitor("Resources/waveformArguments.json")
peakTool = []
trapFeedback = TrapFeedback(waveManager)
Server = Server()
Server.runServer(waveMonitor, waveManager, peakTool, trapFeedback)
