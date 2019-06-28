from Tools.BlackflyCamera import BlackflyCamera
from Tools.Servers import CameraServer
from Tools.peakAnalysisTools import peakAnalysisTools

cameraSerial = 14353509
camera = BlackflyCamera({'serial': cameraSerial})
peakTool = peakAnalysisTools(camera)
Server = CameraServer()
Server.runServer(peakTool)
