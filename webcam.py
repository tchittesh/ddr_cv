import numpy as np
import cv2
from pynput.keyboard import Key, Controller

cap = cv2.VideoCapture(0)

pts1 = []

def get_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        pts1.append([x,y])

cv2.namedWindow('init')
cv2.setMouseCallback('init',get_point)

while(len(pts1) < 4):
    ret, frame = cap.read()

    location = ['bottom left','bottom right','top right','top left'][len(pts1)]
    cv2.putText(frame,'calibration: click the '+location+' corner of your mat',(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),2,cv2.LINE_AA)
    cv2.imshow('init',frame)

    if cv2.waitKey(1) & 0xFF == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit(1)

cv2.destroyWindow('init')

pts1 = np.float32(pts1)
pts2 = np.float32([[300,0],[0,0],[0,300],[300,300]])

homography = cv2.getPerspectiveTransform(pts1,pts2)

threshold = 127

while(True):
    ret, frame = cap.read()

    grid = cv2.warpPerspective(frame,homography,(300,300))
    grid = cv2.cvtColor(grid,cv2.COLOR_BGR2GRAY)
    grid = cv2.GaussianBlur(grid,(3,3),0)
    _,grid = cv2.threshold(grid,threshold,255,cv2.THRESH_BINARY)
    grid = cv2.morphologyEx(grid,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(10,10)))

    cv2.putText(grid,'calibration: use arrow keys to adjust threshold, press enter when done',(10,40),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)

    cv2.imshow('init2',grid)

    k = cv2.waitKey(1)
    if k & 0xFF == 13:
        break
    elif k & 0xFF == 0:
        threshold += 1
    elif k & 0xFF == 1:
        threshold -= 1
    elif k & 0xFF == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit(1)

keyboard = Controller()

feet = [None,None] # positions of feet
grounded = [False,False] # whether or not each foot is on the ground
V_INF = 500
v = [V_INF,V_INF] # velocities of feet
while(True):
    ret, frame = cap.read()

    warped = cv2.warpPerspective(frame,homography,(300,300))
    grid = cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)
    grid = cv2.GaussianBlur(grid,(3,3),0)
    _,grid = cv2.threshold(grid,threshold,255,cv2.THRESH_BINARY)
    grid = cv2.morphologyEx(grid,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(10,10)))

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
    V_THRESH = 5
    for i in range(2):
        if not grounded[i] and feet[i] is not None and v[i] < V_THRESH:
            grounded[i] = True
            square_x = int((feet[i][0]//100)*100)
            square_y = int((feet[i][1]//100)*100)
            warped = cv2.rectangle(warped,(square_x,square_y),(square_x+100,square_y+100),(0,0,0),-1)
            keys = [['q','w','e'],['a','s','d'],['z','x','c']]
            keyboard.press(keys[int(feet[i][1]//100)][int(feet[i][0]//100)])
            keyboard.release(keys[int(feet[i][1]//100)][int(feet[i][0]//100)])
        else:
            grounded[i] = v[i] < V_THRESH

    for i in range(2):
        if feet[i] is not None:
            warped = cv2.circle(warped,(int(feet[i][0]),int(feet[i][1])),(20 if grounded[i] else 10),(0,255,0),-1)
    cv2.imshow('ddr',warped)

    if cv2.waitKey(1) & 0xFF == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit(1)
