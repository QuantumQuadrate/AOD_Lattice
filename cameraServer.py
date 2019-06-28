from Tools.BlackflyCamera import BlackflyCamera
from Tools.Servers import CameraServer
from Tools.peakAnalysisTools import peakAnalysisTools

cameraSerial = 14353509
camera = BlackflyCamera({'serial': cameraSerial})
camera.initialize()
camera.start_capture()
peakTool = peakAnalysisTools(camera)
Server = CameraServer()
Server.runServer(peakTool)
