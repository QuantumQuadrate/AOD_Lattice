import cv2
import numpy as np
from scipy import ndimage
from BlackFlyClient import BlackFlyClient
import matplotlib.pyplot as plt


refPt = []
cropping = False


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
cameraSerial = 14353509
camera = BlackFlyClient(cameraSerial, serverIP)
image = np.true_divide(camera.getImage(), 255)
image = ndimage.rotate(image, rotation)

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

    roi1 = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
    print "Cropping parameters for initial image"
    print refPt
    cv2.imshow("ROI1", roi1)
    cv2.waitKey(0)
