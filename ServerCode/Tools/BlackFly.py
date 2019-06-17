import PyCapture2
import time
from sys import exit
import numpy as np


class BlackFly(object):

    def __init__(self):
        cameraSerial = 15102504# Rubidium's Pointgrey

        triggDelay = 0      # trigger delay in ms
        exposureTime = 2    # exposure time in ms

        timeToSleep = 1000   # time that the computer sleeps between image acquisitions, in ms
        timeToWait = 1000   # time the camera waits for a new trigger before throwing an error, in ms

        bus = PyCapture2.BusManager()
        numCams = bus.getNumOfCameras()

        print "Number of cameras detected: ", numCams
        if not numCams:
            print "Insufficient number of cameras. Exiting..."
            exit()

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
        c.setGigEConfig(enablePacketResend=True, registerTimeoutRetries=3)

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

        settings = {"offsetX": 300, "offsetY": 0, "width": 900, "height": 500, "pixelFormat": PyCapture2.PIXEL_FORMAT.MONO8}
        c.setGigEImageSettings(**settings)
        # Instructs the camera to retrieve only the newest image from the buffer each time the RetrieveBuffer() function is called.
        # Older images will be dropped.
        PyCapture2.GRAB_MODE = 0

        # Sets how long the camera will wait for its trigger, in ms
        c.setConfiguration(grabTimeout=timeToWait)
        c.startCapture()
        self.c = c

    def getImage(self):
        try:
            starttime = time.time()
            image = self.c.retrieveBuffer()
            latency = int(1000 * (time.time() - starttime))
        except PyCapture2.Fc2error as fc2Err:
            print "Error retrieving buffer : ", fc2Err
        try:
            nrows = PyCapture2.Image.getRows(image)   #finds the number of rows in the image data
            ncols = PyCapture2.Image.getDataSize(image)/nrows   #finds the number of columns in the image data
            data = np.array(image.getData())
            reshapeddata = np.reshape(data, (nrows, ncols))
            baseline = np.median(data)
            orienteddata = np.flip(reshapeddata.transpose(1, 0), 1)-baseline #subtract median baseline
        except:
            return "Error"
        return orienteddata
