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
# changes:
# switched UDP to TCP
# random fix

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

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # switched to TCP in preparation for TLS
        self.serverSocket.bind(("127.0.0.1", port))
        self.serverSocket.listen(5)  # Listen for incoming connections

        self.deg = "K"

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

    def processCommands(self, msg, addr):
    		cmds = msg.split(';')
    		for c in cmds:
    			cs = c.split(' ')
    			if len(cs) == 2:  # should be either AUTH or LOGOUT
    				if cs[0] == "AUTH":
    					# Reading our secret
    					password = self.authenticate()
    					if cs[1] == password:
    						with self.token_lock:
    							token = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    							expiration_time = datetime.now() + timedelta(minutes=self.expiration_minutes)
    							# Set token expiration time
    							self.tokens[token] = expiration_time
    						self.serverSocket.sendto(encrypt_value(encryption_key,token).encode("utf-8"), addr)
    				elif cs[0] == "LOGOUT":
    					with self.token_lock: # our lock implemented
    						token = cs[1]
    						if self.tokens.get(token): # using get to prevent keyerrors
    							del self.tokens[token]
    				else:  # unknown command
    					self.serverSocket.sendto(encrypt_value(encryption_key,"Invalid Command\n").encode("utf-8"), addr)
    			elif c[0] in self.prot_cmds:
    				with self.token_lock:
    					authenticate_token = any (token in self.tokens and datetime.now() <= self.tokens[token] for token in cmd[1:]) #check if token is valid and not expired
    					if authenticate_token: #If token is true, check if command is one of the prot_cmds and set the self.deg value
    						if c == "SET_DEGF":
    							self.deg = "F"
    						elif c == "SET_DEGC":
    							self.deg = "C"
    						elif c == "SET_DEGK":
    							self.deg = "K"
    						elif c == "GET_TEMP":
    							self.serverSocket.sendto(encrypt_value(encryption_key,"{}\n".format(self.getTemperature())).encode("utf-8"), addr)
    						elif c == "UPDATE_TEMP":
    							self.updateTemperature()
    						elif c:
    							self.serverSocket.sendto(encrypt_value(encryption_key,"Invalid Command\n").encode("utf-8"), addr)
    					else:
    						self.serverSocket.sendto(encrypt_value(encryption_key, "Authentication Required\n").encode("utf-8"), addr)		
    			else:
    				self.serverSocket.sendto(encrypt_value(encryption_key, "Invalid Command\n").encode("utf-8"), addr)

    def run(self) : #the running function
        while True : 
            try :
                clientSocket, addr = self.serverSocket.accept()
                msg = clientSocket.recv(1024).decode("utf-8").strip()
                cmds = msg.split(' ')
                if len(cmds) == 1 : # protected commands case
                    semi = msg.find(';')
                    if semi != -1 : #if we found the semicolon
                        #print (msg)
                        if msg[:semi] in self.tokens : #if its a valid token
                            self.processCommands(msg[semi+1:], clientSocket)
                        else :
                            clientSocket.send(b"Bad Token\n")
                    else :
                            clientSocket.send(b"Bad Command\n")
                elif len(cmds) == 2 :
                    if cmds[0] in self.open_cmds : #if its AUTH or LOGOUT
                        self.processCommands(msg, clientSocket) 
                    else :
                        clientSocket.send(b"Authenticate First\n")
                else :
                    # otherwise bad command
                    clientSocket.send(b"Bad Command\n")
                    
                clientSocket.close() 

            except IOError as e :
                if e.errno == errno.EWOULDBLOCK :
                    #do nothing
                    pass
                else :
                    #do nothing for now
                    pass
                msg = ""

            self.updateTemperature()
            time.sleep(self.updatePeriod)



class SimpleClient :
    def __init__(self, therm1, therm2) :
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20,50))
        plt.legend(handles=[self.infLn, self.incLn])
        self.infTherm = therm1
        self.incTherm = therm2

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

    def updateTime(self) :
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime) :
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            #last 30 seconds of of data
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times,rotation = 45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))


    def updateInfTemp(self, frame):
        self.updateTime()
        inf_temp = self.infTherm.getTemperature() - 273

        # Connect to the server using TCP and send the temperature update
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
            clientSocket.connect(("127.0.0.1", 23456))
            clientSocket.sendall(str(inf_temp).encode("utf-8"))

        self.infTemps.append(inf_temp)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame):
        self.updateTime()
        inc_temp = self.incTherm.getTemperature() - 273

        # Connect to the server using TCP and send the temperature update
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
            clientSocket.connect(("127.0.0.1", 23457))
            clientSocket.sendall(str(inc_temp).encode("utf-8"))

        self.incTemps.append(inc_temp)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

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