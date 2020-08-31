import cv2

def getProcessedImage(frame, homography, threshold, gridSize):
    grid = cv2.warpPerspective(frame,homography,(gridSize,gridSize))
    grid = cv2.cvtColor(grid,cv2.COLOR_BGR2GRAY)
    grid = cv2.GaussianBlur(grid,(3,3),0)
    _,grid = cv2.threshold(grid,threshold,255,cv2.THRESH_BINARY)
    grid = cv2.morphologyEx(grid,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(int(gridSize/30),int(gridSize/30))))

    return grid

def getThreshold(cap, homography, gridSize):
    '''Calibrate intensity threshold between feet and background.'''
    threshold = 127
    cv2.namedWindow('init2')
    cv2.resizeWindow('init2',600,600)

    while(True):
        _, frame = cap.read()
        grid = getProcessedImage(frame, homography, threshold, gridSize)
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

    cv2.destroyWindow('init2')
    return threshold
