# switched to TCP from UDP in preparation for TLS
# rate limits
# hashicorp vault for token
# error handling for server results and socket

"""
modified the getTemperatureFromPort and authenticate methods to return None on error conditions. This helps in handling errors gracefully and prevents crashes due to unexpected exceptions."""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket

import hvac
import sys
from functools import wraps

from run_vault import get_stored_token
from run_vault import create_vault_client

# Vulnerability 1 rate limiting global constant
RATE_LIMIT = 100  # per second

# Vulnerability 1 we provide a wrapper around functions that contact the server to limit them to maximum RATE_MINUTE calls per second
def rate_limited(max_per_second):
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            elapsed = time.perf_counter() - last_time_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_time_called[0] = time.perf_counter()
            return ret

        return rate_limited_function

    return decorate


class SimpleNetworkClient:
    def __init__(self, port1, port2):
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
        self.infPort = port1
        self.incPort = port2

        self.infToken = None
        self.incToken = None

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

        # Set up the Vault client
        self.vault_client = create_vault_client()

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

    @rate_limited(RATE_LIMIT)
    def getTemperatureFromPort(self, p, tok):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", p))
                s.sendall(b"%s;GET_TEMP" % tok)
                msg = s.recv(1024)
            m = msg.decode("utf-8")
            try:
                temperature = float(m)
                return temperature
            except ValueError:
                print("Received non-numeric value:", m)
                return None  # Vulnerability 3 error handling: Return None on error
        except socket.error as e:
            print("Socket error:", e)
            return None  # Vulnerability 3 error handling: Return None on error

    @rate_limited(RATE_LIMIT)
    def authenticate(self, p, pw):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", p))
                s.sendall(b"AUTH %s" % pw)
                msg = s.recv(1024)
            return msg.strip()
        except socket.error as e:
            print("Socket error:", e)
            return None  # Vulnerability 3 error handling: Return None on error

    def updateInfTemp(self, frame):
        self.updateTime()
        if self.infToken is None:  # not yet authenticated
            self.infToken = self.authenticate(self.infPort, get_stored_token(self.vault_client).encode('utf-8'))

        temperature = self.getTemperatureFromPort(self.infPort, self.infToken)
        
        if temperature is not None and isinstance(temperature, float):
            self.infTemps.append(temperature - 273)
        else:
            print("Discarded non-float temperature:", temperature) # Vulnerability 3 error handling for rate limiting

        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame):
        self.updateTime()
        if self.incToken is None:  # not yet authenticated
            self.incToken = self.authenticate(self.incPort, get_stored_token(self.vault_client).encode('utf-8'))

        temperature = self.getTemperatureFromPort(self.incPort, self.incToken)
        
        if temperature is not None and isinstance(temperature, float):
            self.incTemps.append(temperature - 273)
        else:
            print("Discarded non-float temperature:", temperature) # Vulnerability 3 error handling for rate limiting

        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,


snc = SimpleNetworkClient(23456, 23457)

plt.grid()
plt.show()

