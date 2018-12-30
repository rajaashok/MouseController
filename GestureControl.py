
import time
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
from enum import Enum
import socket

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('localhost', 8089))


class Action(Enum):
	UNKNOWN = 'UNKNOWN'
	LEFT = 'LEFT'
	RIGHT = 'RIGHT'
	CLOSE = 'CLOSE'
	UP = 'UP'
	DOWN = 'DOWN'
	BLINK = 'BLINK'

def eye_aspect_ratio(eye):
	#print(eye[1], eye[5])
	#print(eye[2], eye[4])
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	#print(A, B , C)
	ear = (A + B) / (2.0 * C)
	return ear

def eye_center(eye):
	return (eye[0][1]+eye[1][1]+eye[2][1]+eye[3][1]+eye[4][1]+eye[5][1])/6

def angle_btn_eyes(leftEyePts, rightEyePts):
	# compute the center of mass for each eye
	leftEyeCenter = leftEyePts.mean(axis=0).astype("int")
	rightEyeCenter = rightEyePts.mean(axis=0).astype("int")
 
	# compute the angle between the eye centroids
	dY = rightEyeCenter[1] - leftEyeCenter[1]
	dX = rightEyeCenter[0] - leftEyeCenter[0]
	angle = np.degrees(np.arctan2(dY, dX))
	return angle

def get_positions(cap, detect, predict):
	(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
	(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

	frames = 5
	frame_count = 0

	left_eye_points = []
	right_eye_points = []
	ear_list = []

	while frame_count<=frames:
		frame_count += 1
		ret, frame=cap.read()
		frame = imutils.resize(frame, width=1000)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		subjects = detect(gray, 0)
		for subject in subjects:
			shape = predict(gray, subject)
			shape = face_utils.shape_to_np(shape)#converting to NumPy Array			
			leftEye = shape[lStart:lEnd]
			rightEye = shape[rStart:rEnd]
			
			# Calculate Eye Aspect Ratio
			leftEAR = eye_aspect_ratio(leftEye)
			rightEAR = eye_aspect_ratio(rightEye)
			ear = (leftEAR + rightEAR) / 2.0
			
			print(frame_count)
			left_eye_points.append(eye_center(leftEye))
			right_eye_points.append(eye_center(rightEye))
			ear_list.append(ear)


		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyAllWindows()
			cap.release()
			break
	return np.mean(left_eye_points), np.mean(right_eye_points), np.mean(ear_list)


def fetch_action(cap, detect, predict, left_eye_loc, right_eye_loc, ear_avg):
	thresh = 0.25
	action_frame_check = 5
	closed_frame_check = 20	
	position_check = 10

	(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
	(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
	# register flags for left, right and closed actions
	left_flag=0
	right_flag=0
	up_flag=0
	down_flag=0
	closed_flag=0

	# registering blink
	blink_frame_check = 3
	

	# Set action to unknown
	rec_action = Action.UNKNOWN
	while True:
		ret, frame=cap.read()
		frame = imutils.resize(frame, width=1000)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		subjects = detect(gray, 0)
		for subject in subjects:
			shape = predict(gray, subject)
			shape = face_utils.shape_to_np(shape)#converting to NumPy Array			
			leftEye = shape[lStart:lEnd]
			rightEye = shape[rStart:rEnd]
			# Calculate angle between eyes
			angle_between_eyes = angle_btn_eyes(leftEye, rightEye)
			# Calculate Eye Aspect Ratio
			leftEAR = eye_aspect_ratio(leftEye)
			rightEAR = eye_aspect_ratio(rightEye)
			ear = (leftEAR + rightEAR) / 2.0

			left_center = eye_center(leftEye)
			right_center = eye_center(rightEye)
			#print(left_center, right_center)

			#print(angle_between_eyes, leftEAR, rightEAR, ear)
			if ear < thresh:
				closed_flag += 1
				if closed_flag >= blink_frame_check:
					rec_action = Action.BLINK 
					return rec_action
			elif angle_between_eyes <= -130 and angle_between_eyes >= -175 :
				left_flag += 1
				if left_flag >= action_frame_check:
					rec_action = Action.LEFT 
					return rec_action
			elif angle_between_eyes >= 130 and angle_between_eyes <= 170 :
				right_flag += 1
				if right_flag >= action_frame_check:
					rec_action = Action.RIGHT 
					return rec_action
			elif left_eye_loc < left_center - position_check and right_eye_loc < right_center - position_check :
				down_flag += 1
				if down_flag >= action_frame_check:
					print(left_center, right_center)
					rec_action = Action.DOWN 
					return rec_action
			elif left_eye_loc > left_center + position_check and right_eye_loc > right_center + position_check :
				up_flag += 1
				if up_flag >= action_frame_check:
					print(left_center, right_center)
					rec_action = Action.UP 
					return rec_action
			else:
				flag = 0
				return Action.UNKNOWN
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyAllWindows()
			cap.release()
			break
	return rec_action


cap=cv2.VideoCapture(0)
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


action_ = Action.UNKNOWN
# Sleep to setup Screen recording 
#time.sleep(20)

# capture mean eye locations
left_eye_loc, right_eye_loc, ear_avg = get_positions(cap, detect, predict)
print(left_eye_loc, right_eye_loc, ear_avg)


while action_ != Action.CLOSE:
	#print('Reading')
	action_ = fetch_action(cap, detect, predict, left_eye_loc, right_eye_loc, ear_avg)
	clientsocket.send(action_.value.encode())
	#if action_ != Action.UNKNOWN:
		#time.sleep(3)
	
	#print(action_)
	if action_ == Action.LEFT:
		print('left')
	elif action_ == Action.RIGHT:
		print('right')
	elif action_ == Action.UP:
		print('UP Movement')
	elif action_ == Action.DOWN:
		print('DOWN Movement')
	elif action_ == Action.BLINK:
		print('Blinked.. click here')
		# recompute the person positions
		#left_eye_loc, right_eye_loc, ear_avg = get_positions(cap, detect, predict)	

	#time.sleep(1)


#time.sleep(60)
cv2.destroyAllWindows()
cap.release()

