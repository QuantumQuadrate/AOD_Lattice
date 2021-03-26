from Tools.Servers import CameraServer
from Tools.CameraManager import CameraManager
from Tools.peakAnalysisTools import peakAnalysisTools

cameraSerial = 19287346
camera = CameraManager(cameraSerial)

if camera.cam is None:
    print("Could not find camera  ... not starting server")
else:
    peakTool = peakAnalysisTools(camera)
    Server = CameraServer()
    Server.runServer(peakTool)