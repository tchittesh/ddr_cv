import cv2
import time

cap = cv2.VideoCapture(0)

start = time.time()
t = 0
frames = 0

while (True):
    _, frame = cap.read()
    frames += 1
    cv2.imshow('fps',frame)
    if time.time() - start >= (t+1):
        t += 1
        print(frames)
        frames = 0
    
    if cv2.waitKey(1) & 0xFF == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit(1)

