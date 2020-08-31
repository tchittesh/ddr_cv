import cv2
import numpy as np

def getHomography(cap, gridSize):
    '''Prompt input of four corners and compute homography.'''
    pts1 = []

    def get_point(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            pts1.append([x,y])

    cv2.namedWindow('init')
    cv2.setMouseCallback('init',get_point)

    while(len(pts1) < 4):
        _, frame = cap.read()
        frame = cv2.flip(frame,1) # mirror camera feed for easier UI

        location = ['bottom left','bottom right','top right','top left'][len(pts1)]
        cv2.putText(frame,'calibration: click the '+location+' corner of your mat',(10,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)
        cv2.imshow('init',frame)

        if cv2.waitKey(1) & 0xFF == 27:
            cap.release()
            cv2.destroyAllWindows()
            exit(1)

    cv2.destroyWindow('init')

    # undo flip
    for i in range(4):
        pts1[i][0] = frame.shape[1] - pts1[i][0]

    pts1 = np.float32(pts1)
    pts2 = np.float32([[0,0],[gridSize,0],[gridSize,gridSize],[0,gridSize]])

    return cv2.getPerspectiveTransform(pts1,pts2)
