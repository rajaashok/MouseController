import autopy,pyautogui
import socket,time

move_out_time = 1
avg_move_by=100

def moveRight():
    loc = autopy.mouse.location()
    newloc = [loc[0]+avg_move_by,loc[1]]
    print(loc,newloc)
    pyautogui.moveTo(newloc[0],newloc[1],move_out_time) 


def moveLeft():
    loc = autopy.mouse.location()
    newloc = [loc[0]-avg_move_by,loc[1]]
    print(loc,newloc)
    pyautogui.moveTo(newloc[0],newloc[1],move_out_time)

def moveUp():
    loc = autopy.mouse.location()
    newloc = [loc[0],loc[1]-avg_move_by]
    print(loc,newloc)
    pyautogui.moveTo(newloc[0],newloc[1],move_out_time)    

def moveDown():
    loc = autopy.mouse.location()
    newloc = [loc[0],loc[1]+avg_move_by]
    print(loc,newloc)
    pyautogui.moveTo(newloc[0],newloc[1],move_out_time)

def cleanup(buf):
    if 'BLINK' in buf:
        buf = 'BLINK'
    elif 'LEFT' in buf:
        buf = 'LEFT'
    elif 'RIGHT' in buf:
        buf = 'RIGHT'
    elif 'UP' in buf:
        buf = 'UP'
    elif 'DOWN' in buf:
        buf = 'DOWN'
    elif 'UNKNOWN' in buf:
        buf = 'UNKNOWN'
    return buf

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('localhost', 8089))
serversocket.listen(5) # become a server socket, maximum 5 connections
conn, address = serversocket.accept()
print('Connected by', address)
saved_action='UNKNOWN'
while True:
    #time.sleep(3)
    buf = conn.recv(1024).decode()
    buf = cleanup(buf)

    if len(buf) > 0 and buf != 'UNKNOWN':
        print('buf value:' ,buf, 'saved action:' ,saved_action)

    if saved_action in ['UP','DOWN','RIGHT','LEFT'] and buf=='BLINK':
        saved_action = 'UNKNOWN' 
        buf = 'UNKNOWN'
    elif saved_action == 'UNKNOWN' and buf =='BLINK':
        autopy.mouse.click()
        saved_action = 'UNKNOWN' 
    elif saved_action == 'UNKNOWN' and buf in ['UP','DOWN','RIGHT','LEFT']:
        if buf == 'UP':
            moveUp()
        elif buf == 'DOWN':
            moveDown()
        elif buf == 'RIGHT':
            moveRight()
        elif buf == 'LEFT':
            moveLeft()
        saved_action = buf
    elif saved_action in ['UP','DOWN','RIGHT','LEFT'] and buf in ['UNKNOWN','UP','DOWN','RIGHT','LEFT']:
        if saved_action == 'UP':
            moveUp()
        elif saved_action == 'DOWN':
            moveDown()
        elif saved_action == 'RIGHT':
            moveRight()
        elif saved_action == 'LEFT':
            moveLeft()