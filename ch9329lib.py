#!/usr/bin/env python3
import traceback
import serial
import serial.tools
import serial.tools.list_ports
import serial.tools.hexlify_codec
import binascii
import threading
from socket import socket,AF_INET,SOCK_STREAM

class CH9329CFG:
    packet=bytearray(50)
    workMode=0      #芯片工作模式
    serialMode=0    #串口通信模式
    serialAddress=0       #串口通信地址
    baudrate=9600   #波特率
    reserved0=bytearray(2)
    packetInterval=3         #串口通信包间隔
    usbvid=0x1a86      #USB VID
    usbpid=0xe129      #USB PID
    asciiUploadInterval=0   #ASCII键盘上传间隔
    asciiReleaseInterval=1  #ASCII键盘释放时间
    asciiAutoReturn=False   #ASCII自动回车
    asciiReturnChar=bytearray(8)    #ASCII回车符
    filterStartStopString=bytearray(8)  #过滤开始结束字符
    enableCustomUSBString=0b00000000    #1 个字节芯片 USB 字符串使能标志,
# 位 7:为 0 表示禁止;为 1 表示使能自定义字符串描述符;
# 位 6-3:保留;
# 位 2:为 0 表示禁止;为 1 表示使能自定义厂商字符串描述符;
# 位 1:为 0 表示禁止;为 1 表示使能自定义产品字符串描述符;
# 位 0:为 0 表示禁止;为 1 表示使能自定义序列号字符串描述符;
    asciiFastUpload=False
    reserved1=bytearray(12)
    def __init__(self,packet=bytearray(50)):
        self.workMode=packet[0]
        self.serialMode=packet[1]
        self.serialAddress=packet[2]
        self.baudrate=bytearrayToInt(*packet[3:7])
        self.reserved0=bytearray(packet[7:9])
        self.packetInterval=bytearrayToInt(*packet[9:11])
        self.usbvid=bytearrayToInt(*packet[11:13])
        self.usbpid=bytearrayToInt(*packet[13:15])
        self.asciiUploadInterval=bytearrayToInt(*packet[15:17])
        self.asciiReleaseInterval=bytearrayToInt(*packet[17:19])
        self.asciiAutoReturn=packet[19]>0
        self.asciiReturnChar=bytearray(packet[20:28])
        self.filterStartStopString=bytearray(packet[28:36])
        self.enableCustomUSBString=packet[36]
        self.asciiFastUpload=packet[37]>0
        self.reserved1=bytearray(packet[38:50])
    def toPacket(self):
        packet=bytearray([
        self.workMode,
        self.serialMode,
        self.serialAddress,
        *intToBytearray(self.baudrate,4),
        *self.reserved0,
        *intToBytearray(self.packetInterval,2),
        *intToBytearray(self.usbvid,2),
        *intToBytearray(self.usbpid,2),
        *intToBytearray(self.asciiUploadInterval,2),
        *intToBytearray(self.asciiReleaseInterval,2),
        self.asciiAutoReturn,
        *self.asciiReturnChar,
        *self.filterStartStopString,
        self.enableCustomUSBString,
        self.asciiFastUpload,
        *self.reserved1,
        ])
        return packet
    def __str__(self) -> str:
        output=f"""
        workmode={format(self.workMode, '02x')}
        serialMode={format(self.serialMode, '02x')}
        serialAddress={format(self.serialAddress, '02x')}
        baudrate={self.baudrate}
        reserved0={packetToHexString(self.reserved0)}
        packetInterval={self.packetInterval}
        usbvid={format(self.usbvid, '02x')}
        usbpid={format(self.usbpid, '02x')}
        asciiUploadInterval={self.asciiUploadInterval}
        asciiReleaseInterval={self.asciiReleaseInterval}
        asciiAutoReturn={self.asciiAutoReturn}
        asciiReturnChar={packetToHexString(self.asciiReturnChar)}
        filterStartStopString={packetToHexString(self.filterStartStopString)}
        enableCustomUSBString={format(self.enableCustomUSBString, '08b')}
        asciiFastUpload={self.asciiFastUpload}
        reserved1={packetToHexString(self.reserved1)}
        """
        return output

class CH9329HID:
    #Parameters
    overTCP=False
    debug=False
    path="/dev/ttyUSB0"
    baud=9600
    address=0x00
    #Constants
    __DICT_KEY_NORMAL=dict({
        "esc":0x29,#Esc
        "f1":0x3a,#F1
        "f2":0x3b,#F2
        "f3":0x3c,#F3
        "f4":0x3d,#F4
        "f5":0x3e,#F5
        "f6":0x3f,#F6
        "f7":0x40,#F7
        "f8":0x41,#F8
        "f9":0x42,#F9
        "f10":0x43,#F10
        "f11":0x44,#F11
        "f12":0x45,#F12
        "printscreen":0x46,#Print
        "scrolllock":0x47,#ScrollLock
        "pausebreak":0x48,#PauseBreak
        "`":0x35,#`
        "1":0x1e,#1
        "2":0x1f,#2
        "3":0x20,#3
        "4":0x21,#4
        "5":0x22,#5
        "6":0x23,#6
        "7":0x24,#7
        "8":0x25,#8
        "9":0x26,#9
        "0":0x27,#0
        "-":0x2d,#-
        "=":0x2e,#=
        "~":0x35,#~
        "!":0x1e,#!
        "@":0x1f,#@
        "#":0x20,##
        "$":0x21,#$
        "%":0x22,#%
        "^":0x23,#^
        "&":0x24,#&
        "*":0x25,#*
        "(":0x26,#(
        ")":0x27,#)
        "_":0x2d,#_
        "+":0x2e,#+
        "backspace":0x2a,#Backspace
        "tab":0x2b,#Tab
        "q":0x14,#q
        "w":0x1a,#w
        "e":0x08,#e
        "r":0x15,#r
        "t":0x17,#t
        "y":0x1c,#y
        "u":0x18,#u
        "i":0x0c,#i
        "o":0x12,#o
        "p":0x13,#p
        "[":0x2f,#[
        "]":0x30,#]
        "\\":0x31,#\
        "Q":0x14,#Q
        "W":0x1a,#W
        "E":0x08,#E
        "R":0x15,#R
        "T":0x17,#T
        "Y":0x1c,#Y
        "U":0x18,#U
        "I":0x0c,#I
        "O":0x12,#O
        "P":0x13,#P
        "{":0x2f,#{
        "}":0x30,#}
        "|":0x31,#|
        "caps":0x39,#Caps
        "a":0x04,#a
        "s":0x16,#s
        "d":0x07,#d
        "f":0x09,#f
        "g":0x0a,#g
        "h":0x0b,#h
        "j":0x0d,#j
        "k":0x0e,#k
        "l":0x0f,#l
        ";":0x33,#;
        "'":0x34,#'
        "A":0x04,#A
        "S":0x16,#S
        "D":0x07,#D
        "F":0x09,#F
        "G":0x0a,#G
        "H":0x0b,#H
        "J":0x0d,#J
        "K":0x0e,#K
        "L":0x0f,#L
        ":":0x33,#:
        "\"":0x34,#"
        "enter":0x28,#Enter
        "z":0x1d,#z
        "x":0x1b,#x
        "c":0x06,#c
        "v":0x19,#v
        "b":0x05,#b
        "n":0x11,#n
        "m":0x10,#m
        ",":0x36,#,
        ".":0x37,#.
        "/":0x38,#/
        "Z":0x1d,#Z
        "X":0x1b,#X
        "C":0x06,#C
        "V":0x19,#V
        "B":0x05,#B
        "N":0x11,#N
        "M":0x10,#M
        "<":0x36,#<
        ">":0x37,#>
        "?":0x38,#?
        "space":0x2c,#Space
        "app":0x65,#App
        "menu":0x65,#Menu
        "insert":0x49,#Insert
        "delete":0x4c,#Delete
        "home":0x4a,#Home
        "end":0x4d,#End
        "pageup":0x4b,#PageUp
        "pagedown":0x4e,#PageDown
        "left":0x50,#Left
        "up":0x52,#Up
        "right":0x4f,#Right
        "down":0x51,#Down
        "numlock":0x53,#NumLock
        "numpad/":0x54,#Numpad /
        "numpad*":0x55,#Numpad *
        "numpad-":0x56,#Numpad -
        "numpad+":0x57,#Numpad +
        "numpadenter":0x58,#Numpad Enter
        "numpad1":0x59,#Numpad 1
        "numpad2":0x5a,#Numpad 2
        "numpad3":0x5b,#Numpad 3
        "numpad4":0x5c,#Numpad 4
        "numpad5":0x5d,#Numpad 5
        "numpad6":0x5e,#Numpad 6
        "numpad7":0x5f,#Numpad 7
        "numpad8":0x60,#Numpad 8
        "numpad9":0x61,#Numpad 9
        "numpad0":0x62,#Numpad 0
        "numpad.":0x63,#Numpad .

        })
    __DICT_KEY_CONTROL=dict({
        "lctrl":7,#LCTRL
        "lshift":6,#LSHIFT
        "lalt":5,#LALT
        "lmeta":5,#LMETA
        "lsuper":4,#LSUPER
        "lwin":4,#LWIN
        "rctrl":3,#RCTRL
        "rshift":2,#RSHIFT
        "ralt":1,#RALT
        "rmeta":1,#RMETA
        "rsuper":0,#RSUPER
        "rwin":0,#RWIN
        })
    __DICT_KEY_MEDIA=dict({
        "volup":[0,7],
        "voldown":[0,6],
        "mute":[0,5],
        "playpause":[0,4],
        "nexttrack":[0,3],
        "prevtrack":[0,2],
        "cdstop":[0,1],
        "eject":[0,0],
        "email":[1,7],
        "search":[1,6],
        "wwwfavorite":[1,5],
        "wwwhome":[1,4],
        "wwwback":[1,3],
        "wwwforward":[1,2],
        "wwwstop":[1,1],
        "refresh":[1,0],
        "media":[2,7],
        "explorer":[2,6],
        "calculator":[2,5],
        "screensave":[2,4],
        "mycomputer":[2,3],
        "minimize":[2,2],
        "record":[2,1],
        "rewind":[2,0],
    })
    __NAMES_KEY_CONTROL=[
        "rsuper",#RSUPER/RWIN
        "ralt",#RALT
        "rshift",#RSHIFT
        "rctrl",#RCTRL
        "lsuper",#LSUPER/LWIN
        "lalt",#LALT
        "lshift",#LSHIFT
        "lctrl",#LCTRL
        ]
    __NAMES_KEY_MEDIA=[
        ["eject",
        "cdstop",
        "prevtrack",
        "nexttrack",
        "playpause",
        "mute",
        "voldown",
        "volup",],
        ["refresh",
        "wwwstop",
        "wwwforward",
        "wwwback",
        "wwwhome",
        "wwwfavorite",
        "search",
        "email",],
        ["rewind",
        "record",
        "minimize",
        "mycomputer",
        "screensave",
        "calculator",
        "explorer",
        "media",]
    ]
    __BAUDRATES=[1200,2400,4800,9600,19200,38400,57600,115200]
    #Internal variables
    __port:serial.Serial
    __tcpport:socket
    __pressedKeysCont=[0,0,0,0,0,0,0,0]
    __pressedKeysNormal=bytearray()
    __pressedKeysMedia=[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
    __mousePressByte=0
    def __init__(self,overTCP=False,path="/dev/ttyUSB0",address=0x00,baud=9600,debug=False):
        self.__overTCP=overTCP
        self.path=path
        self.baud=baud
        self.address=address
        self.debug=debug
        self.initPort()
        self.__threadedKeepAlive()
    def isOverTCP(self):
        return self.__overTCP
    def __hexWrite(self,hexdata):
        packet=bytearray()
        for byte in hexdata:
            packet.append(byte)
        if self.__overTCP:
            self.__tcpport.send(packet)
        else:
            self.__port.write(packet)
    def __hexRead(self,size:int):
        output=bytearray()
        if self.__overTCP:
            packet=self.__tcpport.recv(size)
        else:
            packet=self.__port.read(size)
        for byte in packet:
            output.append(byte)
        return output
    def __tcpKeepAlive(self):
        if self.__overTCP:
            self.write9329(0x01,bytearray())
            self.__threadedKeepAlive
    def __threadedKeepAlive(self):
        self.keepAliveThread=threading.Timer(60,self.__tcpKeepAlive)
        self.keepAliveThread.setDaemon(True)
        self.keepAliveThread.start()
    #Port Actions
    def read9329(self):
        try:
            packet=bytearray()
            head=self.__hexRead(5)
            data=self.__hexRead(head[4])
            sumx=self.__hexRead(1)[0]
            packet.extend(head)
            packet.extend(data)
            cmd=packet[3]
            sumy=int()
            for byte in packet:
                sumy+=byte
            sumy=sumy&255
            if sumx==sumy:
                sumpass=True
            else:
                sumpass=False
            packet.append(sumx)
            if self.debug:
                print(f"<- {packetToHexString(packet)},pass:{sumpass}")
            if sumpass:
                if self.debug and cmd==0x81:
                    ver=data[0]
                    usb=data[1]
                    lock="{:0>8b}".format(data[2])
                    info=f"Ver:{hex(ver)},USB:{usb},Num{lock[-1]} Caps{lock[-2]} Scroll{lock[-3]}"
                    print(info)
                return packet
            else:
                return False
        except TimeoutError:
            return False
        except IndexError:
            return False
    def write9329(self,cmd:int,data):
        try:
            packet=bytearray()
            packet.append(0x57)
            packet.append(0xab)
            packet.append(self.address)
            packet.append(cmd)
            if data:
                packet.append(len(data))
                for byte in data:
                    packet.append(byte)
            else:
                packet.append(0)
            sumy=int()
            for byte in packet:
                sumy+=byte
            sumy=sumy&255
            packet.append(sumy)
            self.__hexWrite(packet)
            if self.debug:
                print(f"-> {packetToHexString(packet)}")
            return self.read9329()
        except Exception as exc:
            traceback.print_exc()
            return False
    def initPort(self):
        self.__pressedKeysCont=[0,0,0,0,0,0,0,0]
        self.__pressedKeysNormal=bytearray()
        try:
            if self.__overTCP:
                self.__tcpport = socket(AF_INET, SOCK_STREAM)
                self.__tcpport.settimeout(2)
                pathsplit=self.path.split(":")
                if self.debug:
                    print(f"connecting {pathsplit[0]}:{pathsplit[1] if pathsplit.__len__()>1 else 23}")
                self.__tcpport.connect((pathsplit[0], int(pathsplit[1]) if pathsplit.__len__()>1 else 23))
                return self.__tcpport if self.write9329(0x01,bytearray()) else False
            else:
                self.__port=serial.Serial(port=self.path,baudrate=self.baud)
                self.__port.timeout=2
                return self.__port if self.write9329(0x01,bytearray()) else False
        except Exception as exc:
            traceback.print_exc()
            return False
    def closeSerial(self):
        try:
            self.__port.close()
        except:
            pass
        


    #Keyboard
    def sendKeys(self):
        packet=bytearray()
        packet.append(bitArrayToInt(self.__pressedKeysCont))
        packet.append(0x00)
        data2=bytearray(self.__pressedKeysNormal)
        while len(data2)<6:
            data2.append(0x00)
        for byte in data2:
            packet.append(byte)
        self.write9329(cmd=0x02,data=packet)
        return self.write9329(0x01,bytearray())
    def pressNormal(self,hidcode:int,press=0):
        if press==1:
            if not hidcode in self.__pressedKeysNormal:
                if len(self.__pressedKeysNormal)<=6:
                    self.__pressedKeysNormal.append(hidcode)
                    self.sendKeys()
                    return True
                else:
                    return False
        elif press==-1:
            if hidcode in self.__pressedKeysNormal:
                self.pressNormal(hidcode,0)
            else:
                self.pressNormal(hidcode,1)
        else:
            try:
                self.__pressedKeysNormal.remove(hidcode)
                self.sendKeys()
            except:
                pass
            return True
    def pressControl(self,index:int,press=0):
        self.__pressedKeysCont[index]=1-self.__pressedKeysCont[index] if press==-1 else bool(press)
        self.sendKeys()
        return True
    def pressMedia(self,keyByte:int,keyBit:int,press=0):
        self.__pressedKeysMedia[keyByte][keyBit]= 1-self.__pressedKeysMedia[keyByte][keyBit] if press==-1 else press
        packet=bytearray()
        packet.append(0x02)
        packet.append(bitArrayToInt(self.__pressedKeysMedia[0]))
        packet.append(bitArrayToInt(self.__pressedKeysMedia[1]))
        packet.append(bitArrayToInt(self.__pressedKeysMedia[2]))
        self.write9329(cmd=0x03,data=packet)
        self.write9329(0x01,bytearray())
        return True
    def pressByName(self,name:str,press=0):
        if name in self.__DICT_KEY_NORMAL:
            return self.pressNormal(self.__DICT_KEY_NORMAL[name],press)
        elif name in self.__DICT_KEY_CONTROL:
            return self.pressControl(self.__DICT_KEY_CONTROL[name],press)
        elif name in self.__DICT_KEY_MEDIA:
            return self.pressMedia(self.__DICT_KEY_MEDIA[name][0],self.__DICT_KEY_MEDIA[name][1],press)
        else:
            return False
    def clickByName(self,name:str):
        self.pressByName(name,1)
        self.pressByName(name,0)
    def releaseAll(self):
        self.__pressedKeysCont=[0,0,0,0,0,0,0,0]
        self.__pressedKeysNormal=bytearray()
        self.__pressedKeysMedia=[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
        self.__mousePressByte=0
        self.write9329(cmd=0x02,data=bytearray([0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
        self.write9329(cmd=0x03,data=bytearray([0x00,0x00]))
        self.mouseRel(0,0,0)
    #Mouse
    def setMousePress(self,button:int=0,press:int=1): #Button: left=0,right=1,middle=2,back=3,forward=4,more side buttons=5-7; Press: release=0,press=1,toggle=-1
        if press==0:
            self.__mousePressByte=self.__mousePressByte&(255-(1<<button))
        elif press==1:
            self.__mousePressByte=self.__mousePressByte|(1<<button)
        elif press==-1:
            self.__mousePressByte=self.__mousePressByte^(1<<button)
    def setMouseButtons(self,buttons:int):
        self.__mousePressByte=buttons&255

    def mouseAbs(self,x:int,y:int,wheel:int=0): # x,y = 0~4095
        packet=bytearray([
        (0x02),
        (self.__mousePressByte),
        *intToBytearray(x,2,True),
        *intToBytearray(y,2,True),
        (wheel)])
        return self.write9329(0x04,packet)
    def mouseRel(self,x:int,y:int,wheel:int=0):
        packet=bytearray()
        packet.append(0x01)
        packet.append(self.__mousePressByte)
        if x<0:
            cx=max(x,-127)+0xFF
        else:
            cx=min(x,127)
        if y<0:
            cy=max(y,-127)+0xFF
        else:
            cy=min(y,127)
        packet.append(cx)
        packet.append(cy)
        packet.append(wheel)
        return self.write9329(0x05,packet)
    def mousePressClick(self,button:int=0,press:int=1): #Press=0: release, Press=1: press, Press=2: click, Press=-1: toggle, 
        if press==2:
            self.setMousePress(button,1)
            self.mouseRel(0,0,0)
            self.setMousePress(button,0)
            self.mouseRel(0,0,0)
        else:
            self.setMousePress(button,press)
            self.mouseRel(0,0,0)
    def mousePressButtons(self,buttons:int):
        self.setMouseButtons(buttons)
        return self.mouseRel(0,0,0)
    def mouseReleaseAll(self,immediate=True):
        self.__mousePressByte=0
        if immediate:
            self.mouseRel(0,0,0)
    #Status
    def getPressedKeysRaw(self):
        return self.__pressedKeysNormal,self.__pressedKeysCont,self.__pressedKeysMedia
    def getPressedKeyNormal(self):
        pressed:list[str]
        pressed=[]
        for key in self.__pressedKeysNormal:
            if key in self.__DICT_KEY_NORMAL.values():
                pressed.append(list(self.__DICT_KEY_NORMAL.keys())[list(self.__DICT_KEY_NORMAL.values()).index(key)])
            else:
                pressed.append(hex(key))
        return pressed
    def getPressedKeyCont(self):
        pressed:list[str]
        pressed=[]
        for i in range(self.__pressedKeysCont.__len__()):
            if self.__pressedKeysCont[i]:
                pressed.append(self.__NAMES_KEY_CONTROL[i])
        return pressed
    def getPressedKeyMedia(self):
        pressed:list[str]
        pressed=[]
        for i in range(self.__pressedKeysMedia.__len__()):
            for j in range(self.__pressedKeysMedia[i].__len__()):
                if self.__pressedKeysMedia[i][j]:
                    pressed.append(self.__NAMES_KEY_MEDIA[i][j])
        return pressed
    def getPressedKeyAll(self):
        return self.getPressedKeyNormal(),self.getPressedKeyCont(),self.getPressedKeyMedia()
    def getPressedMouse(self):
        return bin(self.__mousePressByte)
    def getInfo(self):
        return self.write9329(0x01,bytearray())
    #Custom and Config
    def customWrite(self,cmd:str,data:str):
        self.write9329(cmd=int(cmd,16),data=binascii.a2b_hex(data))
    def customHIDWrite(self,data):
        return self.write9329(0x06,data)
    def getConfig(self):
        array=self.write9329(0x08,[])
        if array and array[3]==0x88:
            packet=cropPacket(array)
            return CH9329CFG(packet)
    def setConfig(self,cfg:CH9329CFG):
        return self.write9329(0x09,cfg.toPacket())
    def setUSBString(self,type:int,string:str): #Type: Vendor=0,Product=1,Serial=2
        if len(string)>23:
            return False
        packet=bytearray([type,len(string)])
        packet.extend(bytes(string,"ascii"))
        return self.write9329(0x0b,packet)
    def reset(self):
        return self.write9329(0x0f,None)

# Common utils
def bitArrayToInt(array:list[int]):
    num=0
    for i in array:
        num=(num<<1)+i
    return num
def bytearrayToInt(*args:int,reverse=False):
    num=0
    args2=args
    if reverse:
        args2=args.__reversed__()
    for byte in args2:
        num=(num<<8)+byte
    return num
def intToBytearray(number:int,length:int,reverse=False):
    array=bytearray()
    for i in range(length):
        if reverse:
            array.append(number&255)
        else:
            array.insert(0,number&255)
        number=number>>8
    return array
def cropPacket(packet:bytearray):
    return packet[5:-1]
def packetToHexString(packet):
    showlist=""
    for byte in packet:
        showlist=showlist+(format(byte, '02x'))+" "
    return showlist