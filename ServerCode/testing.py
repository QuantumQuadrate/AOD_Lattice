from Tools.WaveformMonitor import WaveformMonitor
from Tools.WaveformManager import WaveformManager
from Tools.peakAnalysisTools import peakAnalysisTools
from Tools.BlackflyCamera import BlackflyCamera
from Server import Server

camera = BlackflyCamera({})
camera.initialize()
camera.start_capture()

cameraSerial = 14353502
serverIP = "10.140.178.187"
waveManager = WaveformManager("Resources/waveformArguments.json")
waveMonitor = WaveformMonitor("Resources/waveformArguments.json")
peakTool = peakAnalysisTools(camera)
Server = Server()
Server.runServer(waveMonitor, waveManager, peakTool)
