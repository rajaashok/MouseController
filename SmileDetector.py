from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
from enum import Enum


class Action(Enum):
	UNKNOWN = 0
	LEFT = 1
	RIGHT = 2
	CLOSE = 3
	SMILE = 4

def eye_aspect_ratio(eye):
	#print(eye[1], eye[5])
	#print(eye[2], eye[4])
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	#print(A, B , C)
	ear = (A + B) / (2.0 * C)
	return ear

def angle_btn_eyes(leftEyePts, rightEyePts):
	# compute the center of mass for each eye
	leftEyeCenter = leftEyePts.mean(axis=0).astype("int")
	rightEyeCenter = rightEyePts.mean(axis=0).astype("int")
 
	# compute the angle between the eye centroids
	dY = rightEyeCenter[1] - leftEyeCenter[1]
	dX = rightEyeCenter[0] - leftEyeCenter[0]
	angle = np.degrees(np.arctan2(dY, dX))
	return angle

def smile(mouth):
	A = distance.euclidean(mouth[3], mouth[9])
	B = distance.euclidean(mouth[2], mouth[10])
	C = distance.euclidean(mouth[4], mouth[8])
	L = (A+B+C)/3
	D = distance.euclidean(mouth[0], mouth[6])
	mar=L/D
	return mar

def get_average_mar(cap, detect, predict):
	(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
	smile_flag =0 
	frame_check =20
	flag = 0
	mar_list = []

	while True and flag <= frame_check:
		flag += 1
		ret, frame=cap.read()
		frame = imutils.resize(frame, height= 500, width=300)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		subjects = detect(gray, 0)
		for subject in subjects:
			flag += 1
			shape = predict(gray, subject)
			shape = face_utils.shape_to_np(shape)#converting to NumPy Array			
			mouth= shape[mStart:mEnd]
			mar= smile(mouth)
			
			#print('mar value is : ', mar)
			mar_list.append(mar)

		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyAllWindows()
			cap.release()
			break
	return np.mean(mar_list)

def fetch_action(cap, detect, predict, mean_mar):
	(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
	smile_flag =0 
	frame_check =5
	while True:
		ret, frame=cap.read()
		frame = imutils.resize(frame, height= 200, width=200)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		subjects = detect(gray, 0)
		for subject in subjects:
			shape = predict(gray, subject)
			shape = face_utils.shape_to_np(shape)#converting to NumPy Array			
			mouth= shape[mStart:mEnd]
			mar= smile(mouth)
			#mouthHull = cv2.convexHull(mouth)
			#cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)
			#print(mar)
			
			if mar >= mean_mar + 0.05:
				print('mar value is : ', mar, mean_mar )
				smile_flag += 1
				if smile_flag >= frame_check:
					rec_action = Action.SMILE 
					return rec_action
			else:
				flag = 0
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyAllWindows()
			cap.release()
			break
	return rec_action

def highlight(element):
    """Highlights a Selenium webdriver element"""
    driver = element._parent
    style = "border: 4px solid red"
    driver.execute_script("arguments[0].setAttribute('style', arguments[1])", element, style)

def un_highlight(element, orignal_style):
    """Highlights a Selenium webdriver element"""
    driver = element._parent
    driver.execute_script("arguments[0].setAttribute('style', arguments[1])", element, orignal_style)


cap=cv2.VideoCapture(0)
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


chrome_options = Options()
chrome_options.add_argument("--disable-user-media-security=true")
# Enable the kiost option for full screen mode
#chrome_options.add_argument("--kiosk")


# Point chromedriver to the location of the chrome driver executable
chromedriver = "/Users/rnbolla/Documents/FunProjects/2point0/chromedriver"
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chrome_options)

driver.get("https://www.ebay.com/itm/BCP-Kids-12V-Toyota-Tundra-Truck-Ride-On-Car-w-Remote-Control-LED-Lights/312217170773?epid=16022689332&hash=item48b197f355")


#elem = driver.find_element_by_id("search")
title_path='//*[@id="itemTitle"]'
elem = driver.find_elements(By.XPATH, title_path)[0]
sel_element_orig_style  = elem.get_attribute('style')
highlight(elem)
driver.execute_script("arguments[0].scrollIntoView();", elem)
driver.execute_script("window.scrollBy(0, -150);")

action_ = Action.UNKNOWN

buy_now='//*[@id="binBtn_btn"]'
# Sleep to setup Screen recording 
time.sleep(2)

avg_mar = get_average_mar(cap, detect, predict)
print('Mean MAR: ', avg_mar)

while action_ != Action.CLOSE:
	action_ = fetch_action(cap, detect, predict, avg_mar)
	if action_ == Action.SMILE:
		un_highlight(elem, sel_element_orig_style)
		elem = driver.find_elements(By.XPATH, buy_now)[0]
		sel_element_orig_style  = elem.get_attribute('style')
		highlight(elem)
		driver.execute_script("arguments[0].scrollIntoView();", elem)
		driver.execute_script("window.scrollBy(0, -150);")
		time.sleep(3)
		elem.click()

	#time.sleep(1)


time.sleep(60)
driver.quit()
cv2.destroyAllWindows()
cap.release()



#driver.close()