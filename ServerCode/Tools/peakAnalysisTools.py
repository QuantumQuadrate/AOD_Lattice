import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy import ndimage


class peakAnalysisTools(object):

    def __init__(self, camera):
        self.camera = camera
        self.grid = plt.GridSpec(2, 2, wspace=0.4, hspace=0.3)
        self.fig = plt.figure()

    def measureIntensities(self):
        data = {"xAmplitudes": [], "yAmplitudes": []}
        data['xAmplitudes'] = list(self.summedFunctionx[self.peaksx])
        data['yAmplitudes'] = list(self.summedFunctiony[self.peaksy])
        return data

    def getPlot(self, top, bottom, left, right, rotation, cutSizeX, cutSizeY):

        err, grayimg = self.camera.GetImage()
        plt.clf()
        grayimg = ndimage.rotate(grayimg, int(rotation))
        grayimg = grayimg[left:right, top:bottom]
        cutx = self.fig.add_subplot(self.grid[0, 0])
        cuty = self.fig.add_subplot(self.grid[1, 0])
        image = self.fig.add_subplot(self.grid[:, 1])
        image.imshow(grayimg, cmap='gray', vmin=0, vmax=255)
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
        self.summedFunctionx = np.sum(grayimg[:][y0:y1], axis=0)
        grayimg = np.transpose(grayimg)
        self.summedFunctiony = np.sum(grayimg[x0:x1][:], axis=0)

        self.peaksx, properties = find_peaks(self.summedFunctionx, prominence=(200, None))
        self.peaksy, properties = find_peaks(self.summedFunctiony, prominence=(200, None))

        cutx.plot(self.summedFunctionx)
        cutx.plot(self.peaksx, self.summedFunctionx[self.peaksx], "x")
        cuty.plot(self.summedFunctiony)
        cuty.plot(self.peaksy, self.summedFunctiony[self.peaksy], "x")
        cutx.set_ylim([0, 2000])
        cuty.set_ylim([0, 2000])
        return self.fig
