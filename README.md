# ProductIdentifier
<p>
   <img src="https://img.shields.io/badge/backend-Python%203.x-%233776AB?style=flat-square&logo=python"/>&nbsp
   <img src="https://img.shields.io/badge/frontend-Qt-%2341CD52?style=flat-square&logo=qt"/>&nbsp
</p>   

ICT 융합 프로젝트의 일환으로 개발한 상품 분류기입니다.

## 실행 전 요구사항   
   
```Python 3``` 기반으로 작동하며 아래 라이브러리를 필요로 합니다.   

Raspberry Pi
+ paramiko
+ PiCamera
+ PyQt5

Server
+ pillow
+ easyocr

## 실행 방법

실행 전 요구사항에 작성된 라이브러리를 설치한 Python 환경이 필요합니다.   
각 라이브러리의 버전 제한이 있을 수 있으므로 Python 3 환경에서의 실행을 권장하며, 하위 버전에서 실행 시 발생하는 문제는 해결이 어렵습니다.

서버에서는 별도의 하드웨어가 필요하지 않으나 Raspberry Pi와의 안정적인 통신을 위해 이더넷 케이블로의 연결을 권장합니다.   
제어를 수행하는 Raspberry Pi에서는 다음과 같은 하드웨어가 연결되어 있어야 합니다.

GPIO로 연결
+ 컨베이어 모터 드라이버 (모터에 연결됨)
+ 서보 모터 * 2
+ 적외선 근접 센서

별도의 커넥터로 연결
+ Raspberry Pi Camera V2

다음과 같은 환경을 구축한 뒤에 서버에는 ```/server```, Raspberry Pi에서는 ```/raspberrypi``` 디렉터리를 각각 복사합니다.   

그 뒤 SSH 계정 정보를 ```main.py```와 ```identifier.py```에 기록합니다.   
```main.py```파일의 63, 64번 라인을 보면 다음과 같은 내용이 주석 처리되어 있습니다.   
```
# ssh = get_ssh('your ip address', 'your port', 'your account', 'password')
# ssh_execute(ssh, 'python3 'server script path'', is_print=True)
```
이 곳의 주석을 해제한 뒤 Raspberry Pi의 IP 주소, 포트, 계정 이름을 ```get_ssh()```의 인자로 입력합니다.   
또, ```ssh_execute()```의 두 번째 인자인 스크립트를 서버의 스크립트를 가리키도록 다음과 같이 수정합니다.   

예시) ```python3 /home/productidentifier-server/server/identifier.py```

```identifier.py```의 145번 라인에는 Raspberry Pi IP 주소와 계정 정보를 입력합니다.

위 작업이 모두 완료되면 Raspberry Pi에서 ```/raspberrypi/main.py```를 실행합니다.


## 작동 방법

Raspberry Pi에서 스크립트를 실행하면 아래와 같은 화면이 출력됩니다.   
 
![image](https://user-images.githubusercontent.com/66104509/105966823-7d7cf900-60c8-11eb-8c29-10181bdb181b.png)

각 버튼의 사용법은 아래와 같습니다.   

+ 분류기 작동 : 분류기를 작동하며 컨베이어 모터를 가동합니다.
+ 분류기 중지 : 분류기의 작동을 중단하며 컨베이어 모터가 중지됩니다.
+ 디버그 정보 표시 / 숨김 : 구현 예정입니다.

분류기가 작동되면 컨베이어 모터가 가동되며, 컨베이어 모터 상단에 장착된 카메라가 사물을 인식합니다.   
사물이 인식되면 분류를 위해 잠시 컨베이어가 정지하며, 분류가 완료되면 분류 결과와 분류 성공률이 화면에 업데이트됩니다.


## 알려진 문제점

+ 보안 문제   
  스크립트에 계정 이름과 패스워드가 평문으로 노출됨에 따라 인터넷 망에 연결된 장비에는 사용하지 않을 것이 권장됩니다.   
  두 기기 간에 RSA signature를 공유하면 해소됩니다.
  

+ 상태 공유의 부재   
  파일 존재 여부 확인을 통해 우회하여 처리하였으며, 이 과정에서 두 기기 간의 상태가 공유되지 않음에 따라 지연과 불안정한 작동을 유발합니다.
