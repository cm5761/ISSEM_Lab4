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
from collections import deque
from threading import Lock
import hvac

from run_vault import create_vault_client
from run_vault import get_stored_token

import ssl

# changes:
# switched UDP to TCP
# random fix
# DOS/DOS rate fix

MAX_REQUESTS_PER_SECOND = 100
MAX_IPS = 10
TOKEN_EXPIRATION = 7200 # Vulnerability 5 access controls 7200/60 = 120 minutes


class SmartNetworkThermometer (threading.Thread) :
    open_cmds = ["AUTH", "LOGOUT"]
    prot_cmds = ["SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", "UPDATE_TEMP"]

    def __init__ (self, source, updatePeriod, port) :
        threading.Thread.__init__(self, daemon = True) 
        #set daemon to be true, so it doesn't block program from exiting
        self.source = source
        self.updatePeriod = updatePeriod
        self.curTemperature = 0
	self.deg = "K"    
        self.tokens = []

        # After creating the server socket we setup SSL/TLS
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile='server-cert.pem', keyfile='server-key.pem')
        
	# over TCP not UDP
        self.serverSocket = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.serverSocket.bind(("127.0.0.1", port))
        self.serverSocket.listen(5)  # Listen for incoming connections

        # # Vulnerability 1 Dos/DDoS Rate limiter attributes 
        self.max_requests_per_second = MAX_REQUESTS_PER_SECOND
        self.max_ips = MAX_IPS
        self.ip_request_times = {}
        self.ip_locks = {}        

        #Vulnerability #6 Temperature Control
        min_inf_temp = 34+273 # Minimum temperature for infant (93.2°F)
        max_inf_temp = 38+273 # Maximum temperature for infant (100.4°F)
        min_inc_temp = 20+273 # Minimum temperature for incubator (68°F)
        max_inc_temp = 39+273 # Maximum temperature for incubator (102.2°F)

        # Set up the Vault client
        self.vault_client = create_vault_client()
        self.updateTemperature()

    # Vulnerability 5 access controls
    def is_rate_limited(self, ip):
        if ip not in self.ip_request_times:
            self.ip_request_times[ip] = deque(maxlen=self.max_requests_per_second)
            self.ip_locks[ip] = Lock()
            
        with self.ip_locks[ip]:
            request_times = self.ip_request_times[ip]
            current_time = time.time()
            
            # Remove request times older than 1 second
            while request_times and current_time - request_times[0] > 1:
                request_times.popleft()
                
            # Check if the number of requests exceeds the limit
            if len(request_times) >= self.max_requests_per_second:
                return True
            
            # Add the current request time to the deque
            request_times.append(current_time)  # Missing line in your code
            
            return False
            


            
    # Vulnerability 5 access controls
    def generate_token(self):
        # Vulnerability fixing random and using secrets instead
        return ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    
    # Vulnerability 5 access controls
    def is_token_valid(self, token):
        for stored_token in self.tokens:
            if stored_token["token"] == token and (time.time() - stored_token["creation_time"]) <= TOKEN_EXPIRATION:
                return True
        return False

    # Vulnerability 5 access controls and Vulnerability 4 Input Validation
    def process_protected_commands(self, msg, clientSocket, token):
        if not self.is_token_valid(token):
            clientSocket.send(b"Bad Token\n")
            return

        cmds = msg.split(';')
        for c in cmds:
            if c in self.prot_cmds:
                if c == "GET_TEMP":
                    clientSocket.send(b"%f\n" % self.getTemperature())
                elif c == "UPDATE_TEMP":
                    self.updateTemperature()        
                elif c == "SET_DEGF" :
                    self.deg = "F"
                elif c == "SET_DEGC" :
                    self.deg = "C"
                elif c == "SET_DEGK" :
                    self.deg = "K"    
                else:
                    clientSocket.send(b"Invalid Command\n")
            else:
                clientSocket.send(b"Invalid Command\n")

                    
    def setSource(self, source) :
        self.source = source

    def setUpdatePeriod(self, updatePeriod) :
        self.updatePeriod = updatePeriod 

    def setDegreeUnit(self, s) :
        self.deg = s
        if self.deg not in ["F", "K", "C"] :
            self.deg = "K"

    def updateTemperature(self) :
        newTemperature = self.source.getTemperature()
        
        if self.deg == "F":
            min_inf_temp = ((min_inf_temp - 273) * 9 / 5) + 32
            max_inf_temp = ((max_inf_temp - 273) * 9 / 5) + 32	
            min_inc_temp = (min_inc_temp - 273)  * 9 / 5) + 32		
            max_inc_temp = (max_inc_temp - 273)  * 9 / 5) + 32
        elif self.deg == "C":	
            min_inf_temp = min_inf_temp - 273
            max_inf_temp = max_inf_temp - 273	
            min_inc_temp = min_inc_temp - 273		
            max_inc_temp = max_inc_temp - 273		
        
        print("New temperature:", newTemperature - 273)
		
        #Vulnerability #6 Temperature Management
        if self.serverSocket.getsockname()[1] == 23457 and (min_inc_temp > newTemperature or newTemperature > max_inc_temp): 
            print(b"Invalid temperature value (outside of safe incubator range). Please restrict temperature settings to values between 20-39 C. \n")
            print("Your requested value: ", newTemperature)
        elif self.serverSocket.getsockname()[1] == 23456 and (min_inf_temp > newTemperature or newTemperature > max_inf_temp): 
            print(b"Invalid temperature value (outside of safe infant range). Please restrict temperature settings to values between 34-38 C. \n")
            print("Your requested value: ", newTemperature)
        else:
            self.curTemperature = self.source.getTemperature()
		
    def getTemperature(self) :
        if self.deg == "C" :
            return self.curTemperature - 273
        if self.deg == "F" :
            return (self.curTemperature - 273) * 9 / 5 + 32

        return self.curTemperature

    def processCommands(self, msg, clientSocket, ip):
        cmds = msg.split(';')
        for c in cmds:
            cs = c.split(' ')
            if len(cs) == 2:
                if cs[0] == "AUTH":
                    if cs[1] == get_stored_token(self.vault_client):
                        new_token = self.generate_token()
                        self.tokens.append({"token": new_token, "creation_time": time.time()})
                        clientSocket.send(new_token.encode("utf-8"))
                elif cs[0] == "LOGOUT":
                    if cs[1] in [token["token"] for token in self.tokens]:
                        self.tokens = [token for token in self.tokens if token["token"] != cs[1]]
                else:
                    clientSocket.send(b"Invalid Command\n")
            else:
                clientSocket.send(b"Bad Command\n")
                
        # Remove expired tokens
        current_time = time.time()
        self.tokens = [token for token in self.tokens if current_time <= token["creation_time"] + TOKEN_EXPIRATION]





    def run(self):
        while True:
            try:
                clientSocket, addr = self.serverSocket.accept()
                ip, _ = addr
                # Vulnerability 1 Dos/DDoS
                if len(self.ip_request_times) > self.max_ips:
                    clientSocket.send(b"Too many IPs\n")
                    clientSocket.close()
                    continue
                # Vulnerability 1 Dos/DDoS
                if self.is_rate_limited(ip):
                    clientSocket.send(b"Rate limited\n")
                    clientSocket.close()
                    continue

                msg = clientSocket.recv(1024).decode("utf-8").strip()
                cmds = msg.split(' ')
                if len(cmds) == 1:  # protected commands case
                    semi = msg.find(';')
                    if semi != -1:  # if we found the semicolon
                        token = msg[:semi]
                        self.process_protected_commands(msg[semi + 1:], clientSocket, token)
                    else:
                        clientSocket.send(b"Bad Command\n")
                elif len(cmds) == 2:
                    if cmds[0] in self.open_cmds:
                        self.processCommands(msg, clientSocket,ip)
                    else:
                        clientSocket.send(b"Authenticate First\n")
                else:
                    clientSocket.send(b"Bad Command\n")

                clientSocket.close()

            except IOError as e:
                if e.errno == errno.EWOULDBLOCK:
                    pass
                else:
                    pass
                msg = ""

            self.updateTemperature()
            time.sleep(self.updatePeriod)



class SimpleClient:
    def __init__(self, therm1, therm2):
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now - i)) for i in range(30, 0, -1)]
        self.infTemps = [0] * 30
        self.incTemps = [0] * 30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20, 50))
        plt.legend(handles=[self.infLn, self.incLn])
        self.infTherm = therm1
        self.incTherm = therm2

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

        # SSL context for secure communication with disabled hostname and certificate verification
        # ONLY BECAUSE WE DO NOT HAVE A SIGNED CERT TO USE
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='server-cert.pem')
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE

    def updateTime(self):
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime):
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            # last 30 seconds of data
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times, rotation=45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))
            
    # new method encapsulating the secure communication logic
    def secureUpdate(self, thermometer, port):
        temperature = thermometer.getTemperature() - 273
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            with self.context.wrap_socket(s, server_hostname="127.0.0.1") as ssl_socket:
                ssl_socket.connect(("127.0.0.1", port))
                ssl_socket.sendall(str(temperature).encode("utf-8"))

    def updateInfTemp(self, frame):
        self.updateTime()
        self.secureUpdate(self.infTherm, 23456)

        self.infTemps.append(self.infTherm.getTemperature() - 273)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame):
        self.updateTime()
        self.secureUpdate(self.incTherm, 23457)

        self.incTemps.append(self.incTherm.getTemperature() - 273)
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
