from time import sleep
import cv2
import numpy as np
import os
import socket
import threading
import queue
 
q = queue.LifoQueue()
 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tello_address = ('192.168.10.1', 8889)
sock.bind(('0.0.0.0', 9000))
print("Connected")
 
 
testmode = 1 # 1 or 2 for testing features
StepSize = 5
previousDirection = ""
msg = ''
 
 
print("Command")
msg = "command"
msg = msg.encode()
sent = sock.sendto(msg, tello_address)
sleep(2)
 
print("Streamon")
msg = "streamon"
msg = msg.encode()
sent = sock.sendto(msg, tello_address)
sleep(2)
 
 
try:
   if not os.path.exists('data'):
      os.makedirs('data')
except OSError:
   print ('Error: Creating directory of data')
 
if testmode == 1:
   F = open("./data/imagedetails.txt",'a')
   F.write("\n\nNew Test \n")
 
 
def forward():
    msg = "forward 50"
    msg = msg.encode()
    sent = sock.sendto(msg, tello_address)
    print("Going forward")
    sleep(3)
 
def right():
    msg = "cw 90"
    msg = msg.encode()
    sent = sock.sendto(msg, tello_address)
    print ("Going right")
    sleep(3)
    
def left(): 
    msg = "ccw 90"
    msg = msg.encode()
    sent = sock.sendto(msg, tello_address)
    print ("Going left")
    sleep(3)
 
# Not currently used
def backward(): 
    msg = "backward 50"
    msg = msg.encode()
    print ("Going backwards")
    sent = sock.sendto(msg, tello_address)
    sleep(3)   
 
def land():
    msg = "land"
    msg = msg.encode()
    sent = sock.sendto(msg, tello_address)
    print("Landing")
 
 
def getChunks(l, n):
    a = []
 
    for i in range(0, len(l), n):   
 
        a.append(l[i:i + n])
 
    return a
 
 
def Receive():
    currentFrame = 0
    didTakeoff = False
 
    while True:
 
        if didTakeoff == False:
 
            print("takeoff")
            msg = "takeoff"
            msg = msg.encode()
            sent = sock.sendto(msg, tello_address)
            sleep(5)
 
            # Uncomment to have the drone start higher up
            # print("up")
            # msg = "up 75"
            # msg = msg.encode()
            # sent = sock.sendto(msg, tello_address)
            # sleep(5)
 
            didTakeoff = True
 
        name = './data/frame' + str(currentFrame) + '.jpg'
        print ('Creating...' + name)
        
        frame = q.get()
        img = frame.copy()
 
        blur = cv2.bilateralFilter(img,9,40,40) 
        edges = cv2.Canny(blur,50,100) 
 
        img_h = img.shape[0] - 1 
        img_w = img.shape[1] - 1 
 
        EdgeArray = []
 
        for j in range(0,img_w,StepSize): 
 
            pixel = (j,0)
 
            for i in range(img_h-5,0,-1):
 
                if edges.item(i,j) == 255:
 
                    pixel = (j,i) 
                    break 
 
            EdgeArray.append(pixel) 
 
 
        for x in range(len(EdgeArray)-1):
 
            cv2.line(img, EdgeArray[x], EdgeArray[x+1], (0,255,0), 1)
 
 
        for x in range(len(EdgeArray)):
 
            cv2.line(img, (x*StepSize, img_h), EdgeArray[x], (0,255,0), 1)
 
 
        chunks = getChunks(EdgeArray,int(len(EdgeArray)/3))
 
        c = []
 
        for i in range(len(chunks)-1):        
 
            x_vals = []
            y_vals = []
 
            for (x,y) in chunks[i]:
 
                x_vals.append(x)
                y_vals.append(y)
 
 
            avg_x = int(np.average(x_vals))
            avg_y = int(np.average(y_vals))
 
            c.append([avg_y,avg_x]) 
 
            cv2.line(frame, (480,720), (avg_x,avg_y), (255,0,0), 2)
 
        #print("C: ", c)
        forwardEdge = c[1]
        print("Forward Edge[0]: ", forwardEdge[0])
 
        cv2.line(frame, (480,720), (forwardEdge[1], forwardEdge[0]), (0,255,0), 3)
        cv2.imwrite(name, frame)
        
        y = (min(c))
        #print("y[1]: ", y[1])
 
        if forwardEdge[0] > 550: # Can change num to make the drone react closer or farther from object
 
            if y[1] < 310:
 
                if previousDirection == "right":                   
                    right()
                    direction = "right"
                
                else:
                    left()
                    direction = "left"
 
            else: 
 
                if previousDirection == "left":    
                    left()
                    direction = "left"
                
                else:     
                    right()
                    direction = "right"
 
        else:
            forward()
            direction = "forward"
        
        previousDirection = direction
 
        if testmode == 1:
            F.write ("frame" + str(currentFrame)+ ".jpg" + " | " + str(c[0]) + " | " + str(c[1]) + " | " + direction + "\n") 
            currentFrame += 1
 
        if testmode == 2:
            cv2.imshow("frame",frame)
            cv2.imshow("Canny",edges)
            cv2.imshow("result",img)
        
 
if __name__ == '__main__':
    
    p1 = threading.Thread(target=Receive)
    p1.start()
    
    cap = cv2.VideoCapture("udp://@0.0.0.0:11111?overrun_nonfatal=1&fifo_size=50000000")
    while True:
        try:
            ret, frame = cap.read()
            if ret:
                q.put(frame)
                cv2.imshow('Tello', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                land()
                os._exit(1)
        except Exception as err:
            print(err)
    
    cap.release()
    cv2.destroyAllWindows()