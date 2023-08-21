import sys
sys.path.insert(1,'../model/')
from joolpr.infer import LPRModel
import socket
# from serial import Serial
import cv2
import json
import numpy as np
import base64
from datetime import datetime, timezone
import pytz

def get_json_byte(img, number):
    utc = pytz.timezone('UTC')
    kst = pytz.timezone('Asia/Seoul')

    utc_now = datetime.now(utc)
    kst_now = utc_now.astimezone(kst)

    LogData = {"id" : 0, }
    LogData["timeStamp"]=kst_now.strftime("%Y-%m-%d-%H-%M-%S")
    LogData["frame"]=img
    LogData["number"]=number
    LogData["block"]=1

    json_string = json.dumps(LogData)
    json_byte = str.encode(json_string)

    return json_byte

# Replace '/dev/ttyACM0' with the correct port
# arduino = Serial('/dev/ttyACM0', 9600)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# SERVER_IP = "<Your RasPi IP>"
# SERVER_PORT = 12345
# server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_socket.bind((SERVER_IP, SERVER_PORT))
# server_socket.listen()
lpr_model = LPRModel()

while True:
    _, img = cap.read()

    # Server client handling part
    # client_socket, addr = server_socket.accept()
    # print('Connected by', addr)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)


    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) > 100:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = 0 if h == 0 else float(w) / h


                area = w * h
                if 7500 < area < 9500 and 2.3 <= aspect_ratio <= 2.7:
                    boxed_part = img[y:y + h, x:x + w]
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imshow('Boxed Part', boxed_part)
                    number, output_img = lpr_model.infer(boxed_part)
                    print(number)
                    if len(number) == 4:
                        success, buffer = cv2.imencode('.jpg', img)

                        if success:
                            print(type(buffer))
                            encoded_img = base64.b64encode(buffer)
                            print(encoded_img)
                            json_byte = get_json_byte(encoded_img.decode(), number)
                            HOST = "127.0.0.1"  # The server's hostname or IP address
                            PORT = 65432  # The port used by the server

                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.connect((HOST, PORT))
                                s.sendall(json_byte)

                    # client_socket.sendall(b'1')

                    last_x, last_y, last_w, last_h = x, y, w, h


    cv2.imshow("Detected Objects", img)
    cv2.imwrite('result.png', img)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        final_img = img
        final_box = (last_x, last_y, last_w, last_h)
        break

lpr_model.free()
cap.release()
cv2.destroyAllWindows()
# server_socket.close()





# 서버에서 받은 번호판 정보와 모델에서 받은 문자열과 비교
#
# true = servo on
# false = servo init
#
# if true
# 서버에 DetectedRawImg with BoundingBox-> Server