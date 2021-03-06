from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import json
from scipy.signal import find_peaks, peak_prominences




def rgb2gray(rgb):

    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b

    return gray


def func(x, *params):
    y = np.zeros_like(x)
    for i in range(1, len(params), 3):
        ctr = params[i]
        amp = params[i+1]
        wid = params[i+2]
        y = y + amp * np.exp(-((x - ctr)/wid)**2)
    y += params[0]
    return y


def updateAmplitudes(pids, amplitudes):
    with open('waveformArguments.json') as read_file:
        data = json.load(read_file)
    for i in range(len(pids)):
        control = pids[i](amplitudes[i])
        data["Waves"][i]["amplitude"] = control
        print control

    return "done"


left = 90
right = 338
top = 100
bottom = 110
while True:
    cameraImageURL = "http://10.141.230.220/html/cam_pic.php"
    response = requests.get(cameraImageURL)
    img = Image.open(BytesIO(response.content))
    img = img.crop((left, top, right, bottom)) #(left, up, right, bottom)
    grayimg = rgb2gray(np.array(img))
    x = range(right-left)
    plt.clf()
    summedFunction = np.sum(grayimg, axis=0)
    peaks, properties = find_peaks(summedFunction, prominence=(200, None))
    print len(peaks)
    plt.plot(x, summedFunction)
    plt.plot(peaks, summedFunction[peaks], "x")
    #popt, pcov = curve_fit(func, x, summedFunction, p0=guess, maxfev=100000)
    #print popt[1::3]
    #print popt[3::3]
    #fit = func(x, *popt)
    #plt.plot(x, fit
    plt.ylim(0, 2000)
    plt.pause(.05)
plt.show()
