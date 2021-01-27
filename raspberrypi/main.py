import RPi.GPIO as GPIO
import pigpio as PiGPIO
import time
import io
import os
import socket
import struct
import socketserver
import paramiko
import sys
from picamera import PiCamera
from os.path import exists
from PyQt5 import QtGui, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# result file location
RESULT = './result.txt'

# Client IP address
CLIENT_ADDR = ''
PORT = 8000

# DC motor pin number
EN = 16
IN = [20, 21]

# Promixity sensor pin number
PROMIXITY_SENSOR = 24

# Servo motor pin number
SERVO_0 = 18
SERVO_1 = 19

GPIO.setmode(GPIO.BCM)


# GUI

class WindowClass(QtWidgets.QMainWindow):
    def __init__(self):
        super(WindowClass, self).__init__()
        uic.loadUi('ui/controller.ui', self)

        self.image = []

        self.buttonStart.clicked.connect(self.start)
        self.buttonStop.clicked.connect(self.cleanup)
        self.setRate(0)

    def setImage(self, path):
        self.imageLabel.setPixmap(QtGui.QPixmap(path))
        self.imageLabel.repaint()

    def setText(self, text):
        self.resultText.setText(text)
        self.resultText.repaint()

    def setRate(self, rate):
        self.successRate.setValue(rate)

    def start(self):
        # ssh = get_ssh('your ip address', 'your port', 'your account', 'password')
        # ssh_execute(ssh, 'python3 'server script path'', is_print=True)

        imagePath = './image.jpg'
        self.setRate(0)

        # for calculating success rate
        successCount = 0
        total = 0

        try:
            count = 0
            camera = PiCamera()
            motor = Motor(EN, IN)
            promixity = Promixity(PROMIXITY_SENSOR)
            servo1 = Servo(SERVO_0)
            servo2 = Servo(SERVO_1)
            servo1.reset()
            servo2.reset()

            while True:
                if promixity.check_object() == True:
                    isSuccess = False
                    total += 1

                    if checkFileExistence(RESULT):
                        os.remove(RESULT)

                    servo1.reset()
                    servo2.reset()

                    count += 1

                    motor.MotorControl(100, "STOP")

                    # camera.capture('./image'+str(count)+'.jpg')
                    camera.capture(imagePath)
                    time.sleep(1)
                    self.setImage(imagePath)

                    self.setText('사물이 감지되었습니다. 문자를 인식 중입니다.')

                    while not checkFileExistence(RESULT):
                        pass

                    os.remove(imagePath)
                    motor.MotorControl(100, "FORWARD")

                    resultText = ''
                    f = open(RESULT, 'r')
                    lines = f.readlines()
                    for line in lines:
                        resultText += line
                    f.close()
                    print(resultText)

                    self.setText(resultText)

                    if resultText == '서울' or resultText == '경기' or resultText == '인천':
                        servo1.angle1()
                        isSuccess = True
                    elif resultText == '충남' or resultText == '충북' or resultText == '대전':
                        servo1.angle2()
                        isSuccess = True
                    elif resultText == '경남' or resultText == '경북' or resultText == '부산' or resultText == '울산' or resultText == '대구':
                        servo2.angle1()
                        isSuccess = True
                    elif resultText == '전남' or resultText == '전북' or resultText == '광주' or resultText == '강원':
                        servo2.angle2()
                        isSuccess = True
                    else:
                        isSuccess = False

                    if isSuccess == True:
                        successCount += 1

                    successRate = int(successCount / total * 100)

                    self.setRate(successRate)

                    print(successRate)

                    os.remove(RESULT)
                    time.sleep(10)

                else:
                    self.setText('사물을 감지하고 있습니다.')
                    motor.MotorControl(100, "FORWARD")
                    time.sleep(0.1)
                    servo1.reset()
                    servo2.reset()
        except KeyboardInterrupt:
            print("Exception : Keyboard interrupt detected")

        finally:
            print("Shutdown")
            servo1.reset()
            servo2.reset()
            servo1.off()
            servo2.off()
            GPIO.cleanup()

    def cleanup(self):
        print("Shutdown")
        servo1.reset()
        servo2.reset()
        servo1.off()
        servo2.off()
        GPIO.cleanup()


# check if file exists

def checkFileExistence(fileName):
    if os.path.exists(fileName):
        return True
    else:
        return False


# control servo motor
class Servo():
    def __init__(self, PIN):
        self.Servo = PiGPIO.pi()
        self.PIN = PIN
        self.Servo.set_servo_pulsewidth(self.PIN, 0)  # initialization

    def reset(self):
        self.Servo.set_servo_pulsewidth(self.PIN, 500)  # reset servo motor

    def off(self):
        self.Servo.set_servo_pulsewidth(self.PIN, 0)  # turn off servo motor

    def angle1(self):
        self.Servo.set_servo_pulsewidth(self.PIN, 1000)  # set servo motor position to angle 1

    def angle2(self):
        self.Servo.set_servo_pulsewidth(self.PIN, 1600)  # set servo motor position to angle 2


# check object
class Promixity():
    def __init__(self, PIN):
        GPIO.setup(PIN, GPIO.IN)
        self.PIN = PIN
        self.CHECK_ON = 0

    def check_object(self):
        if GPIO.input(self.PIN) == self.CHECK_ON:
            return True
        else:
            return False


# control DC motor
class Motor():
    def __init__(self, EN, IN):
        GPIO.setup(IN, GPIO.OUT)
        GPIO.setup(EN, GPIO.OUT)

        self.IN = IN
        self.pwm = GPIO.PWM(EN, 100)
        self.pwm.start(0)

    def MotorControl(self, speed, stat):
        self.pwm.ChangeDutyCycle(speed)

        if stat == 1 or stat == "FORWARD":  # forward:
            GPIO.output(self.IN[0], GPIO.HIGH)
            GPIO.output(self.IN[1], GPIO.LOW)

        elif stat == 0 or stat == "STOP":  # stop
            GPIO.output(self.IN[0], GPIO.LOW)
            GPIO.output(self.IN[1], GPIO.LOW)

        elif stat == -1 or stat == "BACKWARD":  # backward
            GPIO.output(self.IN[0], GPIO.LOW)
            GPIO.output(self.IN[1], GPIO.HIGH)

        else:
            GPIO.output(self.IN[0], LOW)
            GPIO.output(self.IN[1], LOW)
            print("motor stat err. stat:", stat)


# SSH and SFTP control for paramiko
# Original Code
# https://greenfishblog.tistory.com/258
# modified by 쌀과자 그만 조

# sftp 상에 경로를 생성한다.
# remote 경로가 directory이면, is_dir에 True를 전달한다.
def mkdir_p(sftp, remote, is_dir=False):
    dirs_ = []
    if is_dir:
        dir_ = remote
    else:
        dir_, basename = os.path.split(remote)
    while len(dir_) > 1:
        dirs_.append(dir_)
        dir_, _ = os.path.split(dir_)

    if len(dir_) == 1 and not dir_.startswith("/"):
        dirs_.append(dir_)  # For a remote path like y/x.txt

    while len(dirs_):
        dir_ = dirs_.pop()
        try:
            sftp.stat(dir_)
        except:
            print("making ... dir", dir_)
            sftp.mkdir(dir_)


# sftp 상에 파일을 업로드한다.
# src_path에 dest_path로 업로드한다. 두개 모두 file full path여야 한다.
def file_upload(sftp, src_path, dest_path):
    mkdir_p(sftp, dest_path)
    try:
        sftp.put(src_path, dest_path)
    except Exception as e:
        print("fail to upload " + src_path + " ==> " + dest_path)
        raise e
    print("success to upload " + src_path + " ==> " + dest_path)


# sftp 에서 파일을 다운로드한다.
# src_path에서 dest_path로 다운로드한다.
def file_download(sftp, src_path, dest_path):
    try:
        sftp.get(src_path, dest_path)
        print("success to download " + src_path + " ==> " + dest_path)
    except:
        pass


# sftp 상에 directory를 업로드한다.
# src_directory, dest_directory 모두 directory 경로여야 한다.
# dest_directory에 src_directory가 포함되어 복사된다.
# 즉, src_directory에 CTRL+C, dest_directory에 CTRL+V한 효과가 있다.
def directory_upload(sftp, src_directory, dest_directory):
    mkdir_p(sftp, dest_directory, True)
    cwd = os.getcwd()
    os.chdir(os.path.split(src_directory)[0])
    parent = os.path.split(src_directory)[1]
    is_window = (platform.system() == "Windows")
    for walker in os.walk(parent):
        try:
            for file in walker[2]:
                pathname = os.path.join(dest_directory, walker[0], file)
                if (True == is_window):
                    pathname = pathname.replace('\\', '/')
                    file_upload(sftp, os.path.join(walker[0], file), pathname)
        except Exception as e:
            print(e)
            raise e


# ssh communication

# ssh 명령을 수행한다.
# exit status를 리턴한다.
def ssh_execute(ssh, command, is_print=True):
    # ssh 명령의 결과로 exit status를 구하는게 쉽지 않다.
    # 따라서, 명령의 끝에 "mark=$?"를 출력하여,
    # 최종 exit status를 구할 수 있도록 한다.
    exit_status = 0
    mark = "ssh_helper_result_mark!!@@="
    command = command + ";echo " + mark + "$?"

    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    except Exception as e:
        print(e)
        raise e

    for line in stdout:
        msg = line.strip('\n')
        if (msg.startswith(mark)):
            exit_status = msg[len(mark):]
        else:
            if (True == is_print):
                print(line.strip('\n'))

    return int(exit_status)


def get_ssh(host_ip, port, id, pw):
    try:
        # ssh client 생성
        ssh = paramiko.SSHClient()

        # ssh 정책 설정
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # connect
        ssh.connect(hostname=host_ip, port=port, username=id, password=pw)
    except Exception as e:
        print(e)
        raise e

    return ssh


def get_sftp(ssh):
    try:
        sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    except Exception as e:
        print(e)
        raise e
    return sftp


def close_ssh(ssh):
    ssh.close()


def close_sftp(sftp):
    sftp.close()


def checkFileExistence(fileName):
    if os.path.exists(fileName):
        return True
    else:
        return False


# main

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
