#!/usr/bin/python3
import serial
import RPi.GPIO as GPIO
import datetime
import time


#set led info

LIGHT = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT,GPIO.OUT)


# open serial port


com = serial.Serial("/dev/serial0",baudrate=9600)


#display Send
def displaySend(stringCommand):
    com.write( bytes(stringCommand,encoding="raw_unicode_escape")+b"\xff\xff\xff")

#display rcv part

#do we got three 0xff

threeFF = 0
inBuffer=[]

def  displayReceive():
   global inBuffer
   global threeFF
   while com.inWaiting() > 0:
       v = com.read(1)
       if v == b'\xff':
           threeFF+=1
       else:
           threeFF=0
       inBuffer.append(v)
       if threeFF == 3:
           returnBuffer =  inBuffer[:-3]
           inBuffer=[]
           return True, returnBuffer

   return False, None


#DS18B20  sensor
DS_Sensor1='28-0217c11ee0ff'

def readDS18B20( CapteurId):
   if CapteurId == None:
     return None
   Compteur=0
   while(1):
     try:
       fichier = open( "/sys/bus/w1/devices/" + CapteurId + "/w1_slave")
       texte = fichier.read()
       fichier.close()
       ligne1 = texte.split("\n")[0]
       crc    = ligne1.split("crc=")[1]
       if crc.find("YES")>=0:
        break;
     except:
        #ok une erreur, bouclons
        pass
        time.sleep(1)
     Compteur = Compteur + 1
     if Compteur >= 5 :
       return None

   #ok temp  valid
   ligne2 = texte.split("\n")[1]
   texte_temp = ligne2.split(" ")[9]
   return (float(texte_temp[2:])/1000.0)


lastTime = datetime.datetime.now() - datetime.timedelta(seconds=30)


try:
    while True:

        # read temperature every 30 seconds
        now = datetime.datetime.now()

        if (now - lastTime).total_seconds() > 2:
            lastTime=now
            Temp = readDS18B20(DS_Sensor1)
            print("temperature is ",Temp)
            if Temp is None:
                displaySend("TextTempValue.txt=\"---\"")
            else:
                displaySend("TextTempValue.txt=\"{:2.1f}\xb0C\"".format(Temp))

        flag , buffer = displayReceive()
        if flag:
            #let's decode info
            # 'e' => 0x65  touch event
            if buffer[0] == b'e':
                 #check which page
                 if ord(buffer[1]) == 0:
                     #check if it is press
                     if ord(buffer[3])==1:
                        #check which ID
                         if ord(buffer[2]) ==  2:
                            #this is button ON
                            #turn light ON
                            GPIO.output(LIGHT,1)
                         elif ord(buffer[2]) == 3:
                            #this is button OFF
                            #turn light OFF
                            GPIO.output(LIGHT,0)
        time.sleep(0.010)
except KeyboardInterrupt:
    pass
