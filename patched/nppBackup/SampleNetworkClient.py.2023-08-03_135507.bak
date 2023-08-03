import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket
import hvac
import os
# Run in terminal or separate thread

from setup import * # For testing purposes ONLY

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

        self.url='http://'+decrypt_value(encryption_key,os.environ.get('SET_IP'))+':'+decrypt_value(encryption_key,os.environ.get('SET_PORT'))
        print("PROOF: Decrypted URL: ", self.url) # THIS WOULD NEVER BE IN PRODUCTION, THIS IS FOR ASSIGNMENT
        self.set_token = decrypt_value(encryption_key,os.environ.get('SET_TOKEN')) # THIS WOULD NEVER BE IN PRODUCTION, THIS IS FOR ASSIGNMENT
        print("PROOF: Decrypted Token: ",self.set_token)
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
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        s.sendto(b"%s;GET_TEMP" % tok, (decrypt_value(encryption_key,os.environ.get('SET_IP')), p))
        msg, addr = s.recvfrom(1024)
        m = msg.decode("utf-8")
        return (float(m))

    def authenticate(self, p) :
        #Authenticate with Hashicorp Vault
        client = hvac.Client(url=self.url, token=self.set_token,)
        #Read password from Hashicorp Vault
        read_response = client.secrets.kv.v2.read_secret_version(path=decrypt_value(encryption_key,os.environ.get('SET_PATH')),raise_on_deleted_version=True)
        password = read_response['data']['data']['password']
        print("PROOF: encrypted password: ", password) # THIS WOULD NEVER BE IN PRODUCTION, THIS IS FOR ASSIGNMENT
        password = decrypt_value(encryption_key,password)
        print("PROOF: decrypted password: ", password) # THIS WOULD NEVER BE IN PRODUCTION, THIS IS FOR ASSIGNMENT
        
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        message = encrypt_value(encryption_key,password).encode("utf-8"), (decrypt_value(encryption_key,os.environ.get('SET_IP')), p)
        print("PROOF - MESSAGE SENT: ",message)  # THIS WOULD NEVER BE IN PRODUCTION, THIS IS FOR ASSIGNMENT
        s.sendto(encrypt_value(encryption_key,password).encode("utf-8"), (decrypt_value(encryption_key,os.environ.get('SET_IP')), p) )
        msg, addr = s.recvfrom(1024) # This will crash unless server is running (forcibly close)
        return msg.strip()

    def updateInfTemp(self, frame) :
        self.updateTime()
        if self.infToken is None : #not yet authenticated
            self.infToken = self.authenticate(self.infPort)

        self.infTemps.append(self.getTemperatureFromPort(self.infPort, self.infToken)-273)
        #self.infTemps.append(self.infTemps[-1] + 1)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame) :
        self.updateTime()
        if self.incToken is None : #not yet authenticated
            self.incToken = self.authenticate(self.incPort)

        self.incTemps.append(self.getTemperatureFromPort(self.incPort, self.incToken)-273)
        #self.incTemps.append(self.incTemps[-1] + 1)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

snc = SimpleNetworkClient(23456, 23457)

plt.grid()
plt.show()
snc.authenticate(23456) # Note we will see an error because the server is not running
