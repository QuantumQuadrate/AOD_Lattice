import zmq
import logging
import numpy as np
from BlackflyCamera import BlackflyCamera
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy import ndimage

class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Graph Page!", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

        f = Figure(figsize=(5,5), dpi=100)
        a = f.add_subplot(111)
        a.plot([1,2,3,4,5,6,7,8],[5,6,1,3,8,9,3,5])



        canvas = FigureCanvasTkAgg(f, self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class feedbackServer(object):

    def __init__(self, cameraSerial, settings={}):

        for key in settings:
            self.settings[key] = settings[key]
        grid = plt.GridSpec(2, 2, wspace=0.4, hspace=0.3)
        self.fig = plt.figure()
        rotation = 43
        top = 284
        bottom = 604
        left = 161
        right = 465

        cutSizeX = 30
        cutSizeY = 30
        # a dictionary of instantiated camera objects with serial numbers as
        # the keys
        parameters = {'serial': cameraSerial}
        self.camera = BlackflyCamera(parameters)
        # set up console logging
        self.setup_logger()
        # setup server socket
        self.setup_server()
        # enter poller loop
        self.loop()

    def loop(self):
        """Run the server loop continuously."""
        should_continue = True
        err_msg = "Unexpected exception encountered closing server."
        while should_continue:
            try:
                msg = self.socket.recv_json()
                self.logger.info(msg)
                self.parse_msg(msg)

            except zmq.ZMQError as e:
                if e.errno != zmq.EAGAIN:
                    self.logger.exception(err_msg)
                    break
            except KeyboardInterrupt:
                self.logger.info('Shutting down server nicely.')
                break
            except:
                self.logger.exception(err_msg)
                break
        self.shutdown()

    def parse_msg(self, msg):
        """Parse and act on a request from a client."""
        try:
            action = msg['action']
        except:
            resp = "Unable to parse message from client: {}."
            self.logger.exception(resp.format(msg))
        self.logger.debug('received `{}` cmd'.format(action))

        # register an error as the fall through
        valid = False
        # echo for heartbeat connection verification
        if action == 'ECHO':
            valid = True
            msg['status'] = 0
            self.socket.send_json(msg)

        if action == 'GETPEAKS':
            valid = True
            self.getPeaks(msg)

        if not valid:
            # return the command with bad status and message
            msg['status'] = 1
            error_msg = 'Unrecognized action requested: `{}`'
            msg['message'] = error_msg.format(msg['action'])
            self.socket.send_json(msg)

    def setup_server(self):
        """Initialize the server port and begin listening for instructions."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        # set polling to be short so that the cameras can be checked frequently
        self.socket.setsockopt(zmq.RCVTIMEO, 50)
        addr = "{}://*:{}".format(
            self.settings["protocol"],
            self.settings["port"]
        )
        self.logger.info("server binding to: `{}`".format(addr))
        self.socket.bind(addr)

    def setup_logger(self):
        """Initialize a logger for the server."""
        logger = logging.getLogger(__name__)
        #logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        fmtstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmtstr)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.info('Logger initialized')
        self.logger = logger

    def measureIntensities(self):
        image = self.camera.getImage()
        summedFunction = np.sum(image, axis=0)
        peaks, properties = find_peaks(summedFunction, prominence=(self.peakProminence, None))
        return summedFunction[peaks]

    def shutdown(self):
        """Close the server down."""
        for c in self.cameras:
            self.cameras[c].shutdown()
        self.socket.close()
        self.context.term()

    def displayImage(self, top, bottom, left, right, rotation, cutSizeX, cutSizey):
        grayimg = getImage(cameraSerial, socket)
        plt.clf()
        grayimg = ndimage.rotate(grayimg, rotation)
        grayimg = grayimg[left:right, top:bottom]
        cutx = self.fig.add_subplot(grid[0, 0])
        cuty = self.fig.add_subplot(grid[1, 0])
        image = self.fig.add_subplot(grid[:, 1])
        image.imshow(grayimg)
        dim = grayimg.shape
        x0 = int(dim[0]/2)
        x1 = int(dim[0]/2)+cutSizeX
        y0 = int(dim[1]/2)
        y1 = int(dim[1]/2)+cutSizeY
        print "left to right cut: (transpose)" + str(x0) + " " + str(x1)
        print "top to bottom cut: " + str(y0) + " " + str(y1)
        image.axvline(x0, color='r')
        image.axvline(x1, color='r')
        image.axhline(y0, color='r')
        image.axhline(y1, color='r')
        summedFunctionx = np.sum(grayimg[:][y0:y1], axis=0)
        grayimg = np.transpose(grayimg)
        summedFunctiony = np.sum(grayimg[x0:x1][:], axis=0)

        peaksx, properties = find_peaks(summedFunctionx, prominence=(200, None))
        peaksy, properties = find_peaks(summedFunctiony, prominence=(200, None))

        diff = []
        for i in range(len(peaksx)-1):
            diff += [peaksx[i] - peaksx[i+1]]

        print np.std(diff)
        cutx.plot(summedFunctionx)
        cutx.plot(peaksx, summedFunctionx[peaksx], "x")
        cuty.plot(summedFunctiony)
        cuty.plot(peaksy, summedFunctiony[peaksy], "x")
        cutx.set_ylim([0, 2000])
        cuty.set_ylim([0, 2000])
        plt.pause(.5)


if __name__ == "__main__":
    bfs = feedbackServer()
