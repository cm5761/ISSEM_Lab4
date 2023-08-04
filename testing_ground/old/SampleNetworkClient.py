import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket

import ssl

context = ssl.create_default_context()

class SimpleNetworkClient :
    def __init__(self, port1, port2) :
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
        self.infPort = port1
        self.incPort = port2

        self.infToken = None
        self.incToken = None

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

    def getTemperatureFromPort(self, p, tok) :
        # wrap the socket
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        ssl_socket = context.wrap_socket(s, server_hostname="127.0.0.1")
        # connect to the server
        ssl_socket.connect(("127.0.0.1", p))
        
        ssl_socket.send(b"%s;GET_TEMP" % tok)
        msg = ssl_socket.recv(1024)
        m = msg.decode("utf-8")
        return (float(m))

    def authenticate(self, p, pw) :
        # wrap the socket
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        ssl_socket = context.wrap_socket(s, server_hostname="127.0.0.1")
        # connect to the server
        ssl_socket.connect(("127.0.0.1", p))
        
        ssl_socket.send(b"AUTH %s" % pw)
        msg = ssl_socket.recv(1024)
        return msg.strip()

    def updateInfTemp(self, frame) :
        self.updateTime()
        if self.infToken is None : #not yet authenticated
            self.infToken = self.authenticate(self.infPort, b"!Q#E%T&U8i6y4r2w")

        self.infTemps.append(self.getTemperatureFromPort(self.infPort, self.infToken)-273)
        #self.infTemps.append(self.infTemps[-1] + 1)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame) :
        self.updateTime()
        if self.incToken is None : #not yet authenticated
            self.incToken = self.authenticate(self.incPort, b"!Q#E%T&U8i6y4r2w")

        self.incTemps.append(self.getTemperatureFromPort(self.incPort, self.incToken)-273)
        #self.incTemps.append(self.incTemps[-1] + 1)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30),self.incTemps)
        
snc = SimpleNetworkClient(23456, 23457)

plt.grid()
plt.show()