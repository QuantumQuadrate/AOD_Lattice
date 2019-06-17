import Rb_blackfly_image_gauss as fits
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import urllib2, cStringIO
from PIL import Image
import collections
import PyCapture2
import time
from sys import exit
import thread
import numpy as np

app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget()
win.show()  ## show widget alone in its own window
win.setWindowTitle('Pointgrey Monitor by BG')
view = win.addViewBox()
view.setAspectLocked(True) # lock the aspect ratio so pixels are always square
img = pg.ImageItem()
view.addItem(img)
#
# Main
#

cameraSerial = 15102504# Rubidium's Pointgrey

triggDelay = 0      # trigger delay in ms
exposureTime = 5    # exposure time in ms

timeToSleep = 1000   # time that the computer sleeps between image acquisitions, in ms
timeToWait = 1000   # time the camera waits for a new trigger before throwing an error, in ms

# Ensures sufficient cameras are found
bus = PyCapture2.BusManager()
numCams = bus.getNumOfCameras()
# serial = getCameraSerialNumberFromIndex(1)   #this line not necessary at the moment
print "Number of cameras detected: ", numCams
if not numCams:
    print "Insufficient number of cameras. Exiting..."
    exit()

#c = PyCapture2.Camera()
c = PyCapture2.GigECamera()

# Look up the camera's serial number and pass it to this function:
c.connect(bus.getCameraFromSerialNumber(cameraSerial))

# Powers on the Camera
cameraPower = 0x610
powerVal = 0x80000000
c.writeRegister(cameraPower, powerVal)

# Waits for camera to power up
retries = 10
timeToSleep = 0.1    #seconds
for i in range(retries):
    time.sleep(timeToSleep)
    try:
        regVal = c.readRegister(cameraPower)
    except PyCapture2.Fc2error:    # Camera might not respond to register reads during powerup.
        pass
    awake = True
    if regVal == powerVal:
        break
    awake = False
if not awake:
    print "Could not wake Camera. Exiting..."
    exit()

# Enables resending of lost packets, to avoid "Image Consistency Error"
cameraConfig = c.getGigEConfig()
c.setGigEConfig(enablePacketResend = True, registerTimeoutRetries = 3)

# Configures trigger mode for hardware triggering
print 'configuring trigger mode'
trigger_mode = c.getTriggerMode()
trigger_mode.onOff = True
trigger_mode.mode = 1
trigger_mode.polarity = 1
trigger_mode.source = 0        # Using an external hardware trigger
c.setTriggerMode(trigger_mode)

# Sets the trigger delay
print 'configuring trigger delay'
trigger_delay = c.getTriggerDelay()
trigger_delay.absControl = True
trigger_delay.onOff = True
trigger_delay.onePush = True
trigger_delay.autoManualMode = True
trigger_delay.valueA = 0   #this field is used when the "absControl" field is set to "False"
   #defines the trigger delay, in units of 40.69 ns (referenced to a 24.576 MHz internal clock)
   #range of this field is 0-4095. It's preferred to use the absValue variable.
#trigger_delay.valueB = 0     #I don't know what this value does
trigger_delay.absValue = triggDelay*1e-3   #this field is used when the "absControl" field is set to "True"
   #units are seconds. It is preferred to use this variable rather than valueA
print trigger_delay
c.setTriggerDelay(trigger_delay)


# Sets the camera exposure time using register writes
shutter_address = 0x81C
# "shutter" variable format:
# bit [0]: indicates presence of this feature. 0 = not available, 1 = available
# bit [1]: absolute value control. 0 = control with the "Value" field
                                #  1 = control with the Absolute value register
# bits [2-4]: reserved
# bit [5]: one push auto mode. read: 0 = not in operation, 1 = in operation
#                              write: 1 = begin to work (self-cleared after operation)
# bit [6]: turns this feature on or off. 0 = off, 1 = on.
# bit [7]: auto/manual mode. 0 = manual, 1 - automatic
# bits [8-19]: high value. (not sure what this does)
# bits [20-31]: shutter exposure time, in (units of ~19 microseconds).
bits0_7 = '10000010'
bits8_19 = '000000000000'
shutter_value = int(round((exposureTime*1000+22.08)/18.81))   #converts the shutter exposure time from ms to base clock units
    #in units of approximately 19 microseconds, up to a value of 1000.
    #after a value of roughly 1,000 the behavior is nonlinear
    #max. value is 4095
    #for values between 5 and 1000, shutter time is very well approximated by: t = (value*18.81 - 22.08) us
bits20_31 = format(shutter_value,'012b')
shutter_bin = bits0_7 + bits8_19 + bits20_31
shutter = int(shutter_bin, 2)
c.writeRegister(shutter_address, shutter)

settings= {"offsetX": 0, "offsetY": 0, "width": 1280, "height":960, "pixelFormat": PyCapture2.PIXEL_FORMAT.MONO8}
c.setGigEImageSettings(**settings)
# Instructs the camera to retrieve only the newest image from the buffer each time the RetrieveBuffer() function is called.
# Older images will be dropped.
PyCapture2.GRAB_MODE = 0

# Sets how long the camera will wait for its trigger, in ms
c.setConfiguration(grabTimeout = timeToWait)

# Starts acquisition
c.startCapture()

imageNum = 0
interval = 5 # ms
percentile = 99.5


def updateData():

    try:
        starttime = time.time()
        image = c.retrieveBuffer()
        latency = int(1000 * (time.time() - starttime))
    except PyCapture2.Fc2error as fc2Err:
        print "Error retrieving buffer : ", fc2Err
    try:
        nrows = PyCapture2.Image.getRows(image)   #finds the number of rows in the image data
        ncols = PyCapture2.Image.getDataSize(image)/nrows   #finds the number of columns in the image data
        data = np.array(image.getData())
        reshapeddata = np.reshape(data, (nrows, ncols))
        baseline = np.median(data)
        orienteddata = np.flip(reshapeddata.transpose(1,0),1)-baseline #subtract median baseline
        img.setImage(orienteddata)
        QtCore.QTimer.singleShot(interval, updateData)
    except:
        QtCore.QTimer.singleShot(interval, updateData)

updateData()

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
