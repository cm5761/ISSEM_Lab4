import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import infinc
import time
import math
import socket
import fcntl
import os
import errno

import string
import secrets


from simpleclient import *

import socket
import ssl

host = "127.0.0.1"

# create a custom context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# set the supported ciphers
context.set_ciphers("ECDHE-ECDSA-AES128-GCM-SHA256") #as example

# load the server certificate and private key
context.load_cert_chain("server.crt", "server.key")

class SmartNetworkThermometer (threading.Thread) :
    open_cmds = ["AUTH", "LOGOUT"]
    prot_cmds = ["SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", "UPDATE_TEMP"]

    def __init__ (self, source, updatePeriod, port) :
        threading.Thread.__init__(self, daemon = True) 
        #set daemon to be true, so it doesn't block program from exiting
        self.source = source
        self.updatePeriod = updatePeriod
        self.curTemperature = 0
        self.updateTemperature()
        self.tokens = []

        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        self.ssl_server_socket = context.wrap_socket(server_socket, server_side=True)
        
        fcntl.fcntl(server_socket, fcntl.F_SETFL, os.O_NONBLOCK)

        self.deg = "K"
               


    def processCommands(self, msg, addr) :
        cmds = msg.split(';')
        for c in cmds :
            cs = c.split(' ')
            if len(cs) == 2 : #should be either AUTH or LOGOUT
                if cs[0] == "AUTH":
                    if cs[1] == "!Q#E%T&U8i6y4r2w" :
                        self.tokens.append(''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)))
                        self.ssl_server_socket.send(self.tokens[-1].encode("utf-8"), addr)
                        #print (self.tokens[-1])
                elif cs[0] == "LOGOUT":
                    if cs[1] in self.tokens :
                        self.tokens.remove(cs[1])
                else : #unknown command
                    self.ssl_server_socket.send(b"Invalid Command\n", addr)
            elif c == "SET_DEGF" :
                self.deg = "F"
            elif c == "SET_DEGC" :
                self.deg = "C"
            elif c == "SET_DEGK" :
                self.deg = "K"
            elif c == "GET_TEMP" :
                self.ssl_server_socket.send(b"%f\n" % self.getTemperature(), addr)
            elif c == "UPDATE_TEMP" :
                self.updateTemperature()
            elif c :
                self.ssl_server_socket.send(b"Invalid Command\n", addr)


    def run(self):
        while True:
            try:
                client_socket, addr = self.ssl_server_socket.accept()
                try:
                    msg = client_socket.recv(1024)
                    msg = msg.decode("utf-8").strip()
                    cmds = msg.split(' ')
                    if len(cmds) == 1:  # protected commands case
                        semi = msg.find(';')
                        if semi != -1:  # if we found the semicolon
                            # print (msg)
                            if msg[:semi] in self.tokens:  # if its a valid token
                                self.processCommands(msg[semi + 1:], addr)
                            else:
                                client_socket.send(b"Bad Token\n")
                        else:
                            client_socket.send(b"Bad Command\n")
                    elif len(cmds) == 2:
                        if cmds[0] in self.open_cmds:  # if its AUTH or LOGOUT
                            self.processCommands(msg, addr)
                        else:
                            client_socket.send(b"Authenticate First\n")
                    else:
                        # otherwise bad command
                        client_socket.send(b"Bad Command\n")
                    client_socket.close()

                except IOError as e:
                    if e.errno == errno.EWOULDBLOCK:
                        # do nothing
                        pass
                    else:
                        # do nothing for now
                        pass
                    msg = ""

            except BlockingIOError:
                pass
            
            self.updateTemperature()
            time.sleep(self.updatePeriod)

    def setSource(self, source) :
        self.source = source

    def setUpdatePeriod(self, updatePeriod) :
        self.updatePeriod = updatePeriod 

    def setDegreeUnit(self, s) :
        self.deg = s
        if self.deg not in ["F", "K", "C"] :
            self.deg = "K"

    def updateTemperature(self) :
        self.curTemperature = self.source.getTemperature()

    def getTemperature(self) :
        if self.deg == "C" :
            return self.curTemperature - 273
        if self.deg == "F" :
            return (self.curTemperature - 273) * 9 / 5 + 32

        return self.curTemperature

UPDATE_PERIOD = .05 #in seconds
SIMULATION_STEP = .1 #in seconds

#create a new instance of IncubatorSimulator
bob = infinc.Human(mass = 8, length = 1.68, temperature = 36 + 273)
#bobThermo = infinc.SmartThermometer(bob, UPDATE_PERIOD)
bobThermo = SmartNetworkThermometer(bob, UPDATE_PERIOD, 23456)
bobThermo.start() #start the thread

inc = infinc.Incubator(width = 1, depth=1, height = 1, temperature = 37 + 273, roomTemperature = 20 + 273)
#incThermo = infinc.SmartNetworkThermometer(inc, UPDATE_PERIOD)
incThermo = SmartNetworkThermometer(inc, UPDATE_PERIOD, 23457)
incThermo.start() #start the thread

incHeater = infinc.SmartHeater(powerOutput = 1500, setTemperature = 45 + 273, thermometer = incThermo, updatePeriod = UPDATE_PERIOD)
inc.setHeater(incHeater)
incHeater.start() #start the thread

sim = infinc.Simulator(infant = bob, incubator = inc, roomTemp = 20 + 273, timeStep = SIMULATION_STEP, sleepTime = SIMULATION_STEP / 10)

sim.start()

sc = SimpleClient(bobThermo, incThermo)

plt.grid()
plt.show()

