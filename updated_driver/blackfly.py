import time
import PyCapture2
import numpy


def print_image_info(image):
    """Print image PyCapture2 image object info.

    startCapture callback function for testing.
    """
    # retrieves raw image data from the camera buffer
    raw_image_data = PyCapture2.Image.getData(image)
    # finds the number of rows in the image data
    nrows = PyCapture2.Image.getRows(image)
    # finds the number of columns in the image data
    ncols = PyCapture2.Image.getDataSize(image) / nrows
    # reshapes the data into a 2d array
    data = numpy.reshape(raw_image_data, (nrows, ncols), 'C')
    print (0, nrows, ncols, data)


class BlackflyCamera(object):

    def __init__(self, parameters):
        # initializes the 'data' varable for holding image data
        self.data = []
        self.error = 0
        self.status = 'STOPPED'
        # creates an array to hold camera data for one image
        # self.data.append(numpy.zeros(self.cam_resolution, dtype=float))
        self.area = [(4, 104), (600, 600)]
        # default parameters
        self.parameters = {
            'serial': 14353502,
            'triggerDelay': 0,
            'exposureTime': 1
        }

        for key in parameters:
            self.parameters[key] = parameters[key]
            if key == 'area':
                self.area = parameters['area']

        self.imageNum = 0

    def __del__(self):
        # if self.isInitialized:
        self.powerdown()

    # "initialize()" powers on the camera, configures it for hardware
    # triggering, and starts the camera's image capture process.
    def initialize(self):
        # adds an instance of PyCapture2's camera class
        self.bus = PyCapture2.BusManager()
        self.camera_instance = PyCapture2.GigECamera()
        # connects the software camera object to a physical camera
        self.camera_instance.connect(self.bus.getCameraFromSerialNumber(self.parameters['serial']))

        timeToSleep = 10   # time that the computer sleeps between image acquisitions, in ms
        timeToWait = 1000

        # Powers on the Camera
        cameraPower = 0x610
        powerVal = 0x80000000
        self.camera_instance.writeRegister(cameraPower, powerVal)

        # Waits for camera to power up
        retries = 10
        timeToSleep = 0.1
        for i in range(retries):
            time.sleep(timeToSleep)
            try:
                regVal = self.camera_instance.readRegister(cameraPower)
            except PyCapture2.Fc2error:    # Camera might not respond to register reads during powerup.
                pass
            awake = True
            if regVal == powerVal:
                break
            awake = False
        if not awake:
            print("Could not wake Camera. Exiting...")
            exit()

        # Enables resending of lost packets, to avoid "Image Consistency Error"
        self.camera_instance.setGigEConfig(enablePacketResend=True, registerTimeoutRetries=3)
        exposureTime = 1
        # Configures trigger mode for hardware triggering
        self.configureTriggerMode()
        self.configureTriggerDelay()
        self.configureShutter(exposureTime)
        self.configureCaptureArea()

        # Instructs the camera to retrieve only the newest image from the buffer each time the RetrieveBuffer() function is called.
        # Older images will be dropped.
        PyCapture2.GRAB_MODE = 0

        # Sets how long the camera will wait for its trigger, in ms
        self.camera_instance.setConfiguration(grabTimeout=timeToWait)

    def SetGigEStreamChannel(self, gigEStreamChannel):
        if 'packetSize' in gigEStreamChannel:
            ptype = PyCapture2.GIGE_PROPERTY_TYPE.GIGE_PACKET_SIZE
            gigEProp = self.camera_instance.getGigEProperty(ptype)
            gigEProp.value = gigEStreamChannel['packetSize']
            self.camera_instance.setGigEProperty(gigEProp)
        if 'interPacketDelay' in gigEStreamChannel:
            ptype = PyCapture2.GIGE_PROPERTY_TYPE.GIGE_PACKET_DELAY
            gigEProp = self.camera_instance.getGigEProperty(ptype)
            gigEProp.value = gigEStreamChannel['interPacketDelay']
            self.camera_instance.setGigEProperty(gigEProp)

    # Sets the exposure time
    def SetExposureTime(self, exposureTime):
        """Writes the software-defined exposure time to hardware"""
        shutter_address = 0x81C
        # "shutter" variable format:
        # bit [0]: indicates presence of this feature. 0 = not available, 1 = available
        # bit [1]: absolute value control. 0 = control with the "Value" field
        #                                  1 = control with the Absolute value register
        # bits [2-4]: reserved
        # bit [5]: one push auto mode. read: 0 = not in operation, 1 = in operation
        #                              write: 1 = begin to work (self-cleared after operation)
        # bit [6]: turns this feature on or off. 0 = off, 1 = on.
        # bit [7]: auto/manual mode. 0 = manual, 1 - automatic
        # bits [8-19]: high value. (not sure what this does)
        # bits [20-31]: shutter exposure time, in (units of ~19 microseconds).
        bits0_7 = '10000010'
        bits8_19 = '000000000000'

        # specifies the shutter exposure time
        # in units of approximately 19 microseconds, up to a value of 1000.
        # After a value of roughly 1,000 the behavior is nonlinear.
        # The maximum value is 4095.
        # For values between 5 and 1000, shutter time is very well approximated
        # by: t = (shutter_value*18.81 - 22.08) us
        shutter_value = int(round((exposureTime*1000+22.08)/18.81))
        if shutter_value > 4095:
            shutter_value = 4095
        bits20_31 = format(shutter_value, '012b')
        print(exposureTime)
        print(shutter_value)
        print(bits20_31)
        shutter_bin = bits0_7 + bits8_19 + bits20_31
        # converts the binary value to base-10 integer
        shutter = int(shutter_bin, 2)
        # writes to the camera
        self.camera_instance.writeRegister(shutter_address, shutter)

    # Gets one image from the camera
    def GetImage(self):
        self.error = 0
        self.data = []
        image = False
        try:
            image = self.camera_instance.retrieveBuffer()
        except PyCapture2.Fc2error as fc2Err:
            print(fc2Err)
            print("Error occured. statistics for this shot will be set to NaN")
        if image is not False:
            nrows = PyCapture2.Image.getRows(image)   #finds the number of rows in the image data
            ncols = int(PyCapture2.Image.getDataSize(image)/nrows)   #finds the number of columns in the image data
            data = numpy.array(image.getData())
            reshapeddata = numpy.reshape(data, (nrows, ncols))
            return (self.error, reshapeddata)
        return (1, [])

    def get_data(self):
        data = self.data
        error = self.error
        # clear data and error
        self.data = []
        self.error = 0
        return (error, data)

    def WaitForAcquisition(self):
        # Pauses program for 'pausetime' seconds, to allow the camera to
        # acquire an image
        pausetime = 0.025
        time.sleep(pausetime)

    def powerdown(self):
        cameraPower = 0x610
        powerVal = 0x00000000
        self.camera_instance.writeRegister(cameraPower, powerVal)
        return

    def start_capture(self):
        """Software trigger to begin capturing an image."""
        self.camera_instance.startCapture()
        self.status = 'ACQUIRING'
        self.start_time = time.time()

    def stop_capture(self):
        """Software trigger to stop capturing an image."""
        self.camera_instance.stopCapture()
        self.status = 'STOPPED'

    def shutdown(self):
        try:
            self.camera_instance.stopCapture()
        except:
            print("exception")
        try:
            self.camera_instance.disconnect()
        except:
            print("exception 2")

    def configureTriggerMode(self):
        print('configuring trigger mode')
        trigger_mode = self.camera_instance.getTriggerMode()
        trigger_mode.onOff = False
        trigger_mode.mode = 0
        trigger_mode.polarity = 1
        trigger_mode.source = 0        # Using an external hardware trigger
        self.camera_instance.setTriggerMode(trigger_mode)

    def configureTriggerDelay(self):
        # Sets the trigger delay
        triggDelay = 10      # trigger delay in ms
        print('configuring trigger delay')
        trigger_delay = self.camera_instance.getTriggerDelay()
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
        self.camera_instance.setTriggerDelay(trigger_delay)

    def configureShutter(self, exposureTime):

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
        self.camera_instance.writeRegister(shutter_address, shutter)

    def configureCaptureArea(self):
        settings = {"offsetX": self.area[0][0], "offsetY": self.area[0][1], "width": (self.area[1][0]-self.area[0][0]), "height": (self.area[1][1]-self.area[0][1]), "pixelFormat": PyCapture2.PIXEL_FORMAT.MONO8}
        # settings['height'] = int(self.area[1][1]-self.area[0][1])
        # settings['offsetX'] = int(self.area[0][0])
        # settings['offsetY'] = int(self.area[0][1])
        # settings['width'] =
        # settings = {"offsetX": offsetX, "offsetY": offsetY, "width": width, "height": height, "pixelFormat": PyCapture2.PIXEL_FORMAT.MONO8}
        # settings = {"offsetX": self.area[0][0], "offsetY": self.area[0][1], "width": 100, "height": 100, "pixelFormat": PyCapture2.PIXEL_FORMAT.MONO8}
        print(settings)
        self.camera_instance.setGigEImageSettings(**settings)



cameraSerial = 14353509
camera = BlackflyCamera({'serial': cameraSerial,
                     'area': [(0, 0), (800, 600)]})
camera.initialize()
camera.start_capture()


def get_image():

    data = camera.GetImage()
    image = data[1]
    #from matplotlib import pyplot as plt
    #plt.imshow(image)
    #plt.show()
    return image


from io import BytesIO
import numpy as np
from flask import Flask, jsonify, make_response, send_file
import sys
from PIL import Image
import threading




app = Flask(__name__)



@app.route('/get_image')
def  get_image_route():
    start = time.time()
    image = get_image()
    print("time to capture image:{}".format(time.time() - start), file=sys.stderr)
    buffer = BytesIO()
    np.savez_compressed(buffer, image=image)

    buffer.seek(0)
    resp = make_response(buffer.getvalue())
    return resp


    #return send_file(buffer, mimetype="application/x-binary")

@app.route('/get_image_png')
def  get_image_png_route():
    start = time.time()
    image = get_image()
    print("time to capture image:{}".format(time.time() - start), file=sys.stderr)
    buffer = BytesIO()

    im = Image.fromarray(image)
    im.save(buffer, format="PNG")

    buffer.seek(0)
    resp = make_response(buffer.getvalue())
    resp.mimetype="image/png"
    return resp

@app.route('/get_image_png_norm')
def  get_image_png_norm_route():
    image = get_image()
    buffer = BytesIO()

    image = (image - image.min())/(image.max() - image.min())
    image = (image*255).astype(np.uint8)

    im = Image.fromarray(image)
    im.save(buffer, format="PNG")

    buffer.seek(0)
    resp = make_response(buffer.getvalue())
    resp.mimetype="image/png"
    return resp



if __name__ == "__main__":
    app.run(host='0.0.0.0')

"""
if __name__ == "__main__":
    cameraSerial = 14353509
    camera = BlackflyCamera({'serial': cameraSerial,
                             'area': [(0, 0), (800, 600)]})
    camera.initialize()
    camera.start_capture()

    data = camera.GetImage()
    image = data[1]
    from matplotlib import pyplot as plt

    plt.imshow(image)
    plt.show()
"""