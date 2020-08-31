import numpy as np
import cv2
import time
from pynput.keyboard import Key, Controller

from getHomography import getHomography
from getThreshold import getThreshold, getProcessedImage

# PARAMETERS
gridSize = 99 # size of warped image to do all calculations on (multiple of 3)
V_THRESH = 1.5 # threshold velocity to register as off the ground

cap = cv2.VideoCapture(0)

# Calibration
homography = getHomography(cap,gridSize)
threshold = getThreshold(cap,homography,gridSize)

keyboard = Controller()

cv2.namedWindow('ddr')
cv2.resizeWindow('ddr',600,600)

feet = [None,None] # positions of feet
grounded = [False,False] # whether or not each foot is on the ground
keysPressed = [None,None] # contains value of key pressed by feet[i] if grounded[i] is true
V_INF = gridSize + 100
v = [V_INF,V_INF] # velocities of feet
keys = [['q','w','e'],['a','s','d'],['z','x','c']]
# variables used to track FPS
startTime = time.time()
t = 0
frames = 0
fps = 0

while(True):
    _, frame = cap.read()
    grid = getProcessedImage(frame, homography, threshold, gridSize)
    warped = cv2.warpPerspective(frame,homography,(gridSize,gridSize))

    n,labels,stats,centroids = cv2.connectedComponentsWithStats(np.uint8(grid))
    feet_idx = [1,2]
    for i in range(3,n):
        if stats[i,cv2.CC_STAT_AREA] > stats[feet_idx[0],cv2.CC_STAT_AREA]:
            feet_idx[0] = i
        elif stats[i,cv2.CC_STAT_AREA] > stats[feet_idx[1],cv2.CC_STAT_AREA]:
            feet_idx[1] = i

    # match feet to previous locations
    # update feet and v
    if n == 1: # no feet found
        v = [V_INF,V_INF]
        feet = [None,None]
    elif n == 2: # one foot found
        v00 = V_INF if feet[0] is None else np.linalg.norm(feet[0]-centroids[1])
        v10 = V_INF if feet[1] is None else np.linalg.norm(feet[1]-centroids[1])
        if v00 <= v10:
            v = [v00,V_INF]
            feet = [centroids[1],None]
        else:
            v = [V_INF,v10]
            feet = [None,centroids[1]]
    else: # both feet found
        v00 = V_INF if feet[0] is None else np.linalg.norm(feet[0]-centroids[feet_idx[0]])
        v11 = V_INF if feet[1] is None else np.linalg.norm(feet[1]-centroids[feet_idx[1]])
        v01 = V_INF if feet[0] is None else np.linalg.norm(feet[0]-centroids[feet_idx[1]])
        v10 = V_INF if feet[1] is None else np.linalg.norm(feet[1]-centroids[feet_idx[0]])
        if v00+v11 <= v01+v10:
            v = [v00,v11]
            feet = [centroids[feet_idx[0]],centroids[feet_idx[1]]]
        else:
            v = [v01,v10]
            feet = [centroids[feet_idx[1]],centroids[feet_idx[0]]]

    # register steps
    # update grounded
    # TODO: enable stepping on multiple buttons
    for i in range(2):
        if not grounded[i] and feet[i] is not None and v[i] < V_THRESH:
            keysPressed[i] = keys[int(feet[i][1]//(gridSize/3))][int(feet[i][0]//(gridSize/3))]
            keyboard.press(keysPressed[i])
        elif grounded[i] and (feet[i] is None or v[i] >= V_THRESH):
            keyboard.release(keysPressed[i])
            keysPressed[i] = None
        grounded[i] = v[i] < V_THRESH

    # update FPS
    frames += 1
    if time.time() - startTime >= (t+1):
        t += 1
        fps = frames
        frames = 0
    cv2.putText(warped,'fps: '+str(fps),(10,50),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),2,cv2.LINE_AA)

    # visualize state
    for i in range(2):
        if feet[i] is not None:
            warped = cv2.circle(warped,(int(feet[i][0]),int(feet[i][1])),(int(gridSize/15) if grounded[i] else int(gridSize/30)),(0,255,0),-1)
    cv2.imshow('ddr',warped)
    
    if cv2.waitKey(1) & 0xFF == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit(1)
    elif cv2.waitKey(1) & 0xFF == ord('r'):
        threshold = getThreshold(cap,homography,gridSize)
