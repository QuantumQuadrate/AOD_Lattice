import cv2
import numpy as np
from scipy import ndimage
from BlackFlyClient import BlackFlyClient
import matplotlib.pyplot as plt
import math

refPt = []
cropping = False


def roundup(x):
    return int(math.ceil(x / 10.0)) * 10


def click_and_crop(event, x, y, flags, param):
    global refPt, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:

        refPt.append((x, y))
        cropping = False

        cv2.rectangle(image, refPt[0], refPt[1], (255, 255, 255), 2)
        cv2.imshow("image", image)


rotation = 43
serverIP = "10.140.178.187"
cameraSerial = 14353502
camera = BlackFlyClient(cameraSerial, serverIP, [(0, 0), (808, 608)])

image = np.true_divide(camera.getImage(), 255)
plt.imshow(camera.getImage())
plt.show()
# out = np.zeros(image.shape, np.double)
# image = cv2.normalize(image, out, 0.0, 1.0, cv2.NORM_MINMAX)
print image

clone = image.copy()

cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)

while True:
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("r"):
        image = clone.copy()
    elif key == ord("c"):
        break

if len(refPt) == 2:
    roiPts = [[1, 2], [3, 4]]
    for i in range(2):
        for j in range(2):
            roiPts[i][j] = roundup(refPt[i][j])
    roi1 = clone[roiPts[0][1]:roiPts[1][1], roiPts[0][0]:roiPts[1][0]]
    print "Cropping parameters for initial image"
    print roiPts
    roi1 = grayimg = ndimage.rotate(roi1, rotation)
    clone = roi1.copy()
    cv2.imshow("ROI1", roi1)

    image = roi1

    cv2.imshow("image", image)
    cv2.setMouseCallback("image", click_and_crop)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("r"):
            roi1 = clone.copy()
        elif key == ord("c"):
            break
    if len(refPt) == 2:
        roi2 = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
        cv2.imshow("ROI2", roi2)
        print "Cropping parameters for rotated image"
        print refPt
    cv2.waitKey(0)
