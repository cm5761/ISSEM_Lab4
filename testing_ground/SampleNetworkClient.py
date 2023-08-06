import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket

from functools import wraps

#changes:
# switched to TCP from UDP in preparation for TLS
# rate limits

RATE_LIMIT = 100 #per second

# we provide a wrapper around functions that contact the server to limit them to maximum RATE_MINUTE calls per second
def rate_limited(max_per_second):
    min_interval = 1.0 / float(max_per_second)
    def decorate(func):
        last_time_called = [0.0]
        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            elapsed = time.perf_counter()- last_time_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_time_called[0] = time.perf_counter()
            return ret
        return rate_limited_function
    return decorate

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

    @rate_limited(RATE_LIMIT)
    def getTemperatureFromPort(self, p, tok) :
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", p))
            s.sendall(b"%s;GET_TEMP" % tok)
            msg = s.recv(1024)
        m = msg.decode("utf-8")
        return (float(m))

    @rate_limited(RATE_LIMIT)
    def authenticate(self, p, pw) :
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", p))
            s.sendall(b"AUTH %s" % pw)
            msg = s.recv(1024)
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
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

snc = SimpleNetworkClient(23456, 23457)

plt.grid()
plt.show()
