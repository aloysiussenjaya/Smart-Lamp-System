# Import necessary library
import cv2
import numpy as np
import socket
import time


# Define IP Address for Arduinos
Arduino_1 = '192.168.43.137'
Arduino_2 = '192.168.43.87'

# Define Port Number
PORT = 8888

# Class to provide function that use for socket programming
class Connection:

    # Initialize function to initialize class 
    # Input : HOST - IP Address
    #         PORT - Port Number
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
    
    # Function to create the new socket
    # Output : socket based on give address family and socket type
    def createSocket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create Socket using the given address family and socket type 
    
    # Function to connect the socket
    # Input : sock - socket that was created before 
    def connect(self, sock):
        server_address = (self.HOST, self.PORT)
        print('connecting to {} port {}'.format(*server_address))
        sock.connect(server_address) # Connect to a remote socket at address 
    
    # Function to send packet
    # Input : message - data bytes
    #         sock - socket that was created before
    def sendPacket(self, message, sock):
        print('sending {!r}'.format(message))
        sock.sendall(message) # Send data to the socket that socket must be connected to the remote socket 
    
    # Function to close the socket 
    # Input : sock - socket that was created before
    def closeSocket(self, sock):
        print('closing socket')
        sock.close() # Close socket

# Function to determine which Arduino would receive connection and the data
def clientSocket(msg, lamp):
    if lamp == 1:
        tcpConnection = Connection(Arduino_1, PORT)
    elif lamp == 2:
        tcpConnection = Connection(Arduino_2, PORT)
    else: 
        print('Error')

    sock = tcpConnection.createSocket() # Create the socket 
    tcpConnection.connect(sock) # Connect to the remote socket

    try:
        tcpConnection.sendPacket(msg, sock) # Send the data to the socket 
        
    finally:
        data = sock.recv(200).decode() # Receive data from the socket with parameter buffer size that control maximum amount of data to be received at once.
        print('received {!r}'.format(data))
        tcpConnection.closeSocket(sock) # Close the socket

        
confidence_threshold = 0.45 # A threshold used to filter boxes by confidences
nms_threshold = 0.2 # A threshold used in non maximum suppression.

classNames= [] # Array of string that contains label of classification 
classFile = 'coco.names' # Path to file that contain the label of classification

with open(classFile,'rt') as f: # Open file with reading text mode 
    classNames = f.read().rstrip('\n').split('\n') # Read text line by line and inject to the array


# Path to file that contain the trained model for dnn
configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = 'frozen_inference_graph.pb'

# Initialize the constant to calculate distance of the detected object with camera.
known_distance = 150 # Real distance the sample 
known_frame_height = 388 # Average frame height of sample based on real distance
real_sample_height = 167 # Average height of sample 

# Load the network for neural network
net = cv2.dnn_DetectionModel(weightsPath,configPath)
# Set the preprocessing properties
net.setInputSize(320,320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Function to calculate the focal length 
# Input : known_distance - Real distance the sample 
#         real_sample_height - Average height of sample
#         known_frame_height - Average frame height of sample based on real distance
# Output : focal_length
def getFocalLength(known_distance, real_sample_height, known_frame_height):
    focal_length = (known_frame_height * known_distance) / real_sample_height
    return focal_length

# Function to calculate distance of the detected object with camera.
# Input : Focal_length
#         real_sample_height - Average height of sample
#         real_time_frame_height - Frame height of detected object at that time
# Output : result - distance of the detected object with camera.
def calculateDistance(Focal_length, real_sample_height, real_time_frame_height):
    result = (real_sample_height * Focal_length) / real_time_frame_height
    return result

# Function to detect object within the detected frame 
# Input : img - captured frame from the video source
#         objects - list of classification label from COCO names 
# Output : img - the processed frame
#          objectInfo - Set of bounding box value and label of the classification
def getObjects(img, draw=True, objects=[]):
    # Run net and return result detections with given frame input and confidence threshold. 
    # img - The input image.
    # classIds - Class indexes in result detection.
    # confidences - A set of corresponding confidences.
    # confidence_threshold	A threshold used to filter boxes by confidences.
    # nms_threshold	A threshold used in non maximum suppression.
    classIds, confidences, bboxes = net.detect(img,confThreshold=confidence_threshold) 
    bboxes = list(bboxes) # A set of bounding boxes.

    # A set of corresponding confidences.
    confidences = list(np.array(confidences).reshape(1,-1)[0]) 
    confidences = list(map(float, confidences))

    # If didn't state for specify label, the objects array will automatically filled by all label on the classNames array
    if len(objects) == 0:
        objects = classNames

    objectInfo = [] # A set of object info that contains bounding box value and label of the classification. 

    indices = cv2.dnn.NMSBoxes(bboxes, confidences, confidence_threshold, nms_threshold) # Perform non max suppresion given boxes and corresponding confidences.

    for i in indices:
        i = i[0]
        box = bboxes[i] # Bounding box
        prob = confidences[i] # Computer confidence score while detecting a objects.
        x,y,w,h = box[0],box[1],box[2],box[3]
        
        className = classNames[classIds[i][0]-1]
        if className in objects:
            if prob > 0.65:
            # The code below would run if the prob higher than 0.65
            objectInfo.append([[x,y,w,h], className]) # Add the bounding box value and label of the classification to the array.
            if(draw):
                cv2.rectangle(img, (x,y), (x+w,y+h), color=(0,225,0), thickness=2) # Draw rectangle (bounding box) around the detected object.
                cv2.putText(img, className.upper(), (box[0]+10, box[1]+30), cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2) # Draw text (label of the classification) on the top left corner of the bounding box.

    return img, objectInfo
    

if __name__ == "__main__":
    cap = cv2.VideoCapture(0) # Access the video source
    cap.set(3,640) # Set width of the frames in the video stream.
    cap.set(4,480) # Set height of the frames in the video stream.
    cap.set(5,60)  # Set frame rate.
    cap.set(cv2.CAP_PROP_BUFFERSIZE,1) # Set buffer size 
    cap.set(10,60) # Set brightness of the image (only for cameras).
    while True:
        success,img = cap.read() # Read the frame of video source 
        # Process the frame (image) of the video source 
        result, objectInfo = getObjects(img,objects=['person']) # Determine the label of the classification on COCO that you want to use.
        if not objectInfo: # The system not detect any person.
            print("Null")
        else :
            for final_box in objectInfo:
                frame_height = final_box[0][3] # Get the frame heigh of the bounding box.
                if frame_height != 0:
                    # The code below would run if the frame height isn't equal 0.
                    focal_length = getFocalLength(known_distance, real_sample_height, known_frame_height) # Get the focal length value
                    Distance = calculateDistance(focal_length, real_sample_height, height) + 25 # Calculate the distance of the detected object by the system at that time on centimeters.
                    if (Distance > 149.9) and (Distance < 249.9):
                        clientSocket(b'0', 1) # Give command to turn on the first lamp 
                        clientSocket(b'1', 2) # Give command to turn off the second lamp
                        time.sleep(0.3) # Delay 0.3 second
                    elif (Distance > 349.9) and (Distance < 449.9):
                        clientSocket(b'0', 2) # Give command to turn on the second lamp
                        clientSocket(b'1', 1) # Give command to turn off the first lamp 
                        time.sleep(0.3) # Delay 0.3 second
                    else:
                        clientSocket(b'1', 1) # Give command to turn off the first lamp 
                        clientSocket(b'1', 2) # Give command to turn off the second lamp
                        time.sleep(0.3) # Delay 0.3 seconds
                        
                else:
                    clientSocket(b'1', 1) # Give command to turn off the first lamp 
                    clientSocket(b'1', 2) # Give command to turn off the second lamp
                    time.sleep(0.3) # Delay 0.3 seconds

            # Uncomment code below if you need for debugging.                    
            # print(objectInfo) 
        
            
        cv2.imshow("Output",img) # To show the footage from the camera on screen.
        key = cv2.waitKey(1) & 0xFF # Get the value for pressed key.

        # If Q on the keyboard was pressed then program would stop.
        if key == ord("q"):
            break