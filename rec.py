import pymongo
import json
from scapy.all import TCP,IP,sniff,send,Raw
import socket

url="mongodb://localhost:27017/"
client=pymongo.MongoClient(url)
db=client["SIH"]
col=db["data"]
def packetBuilder():
    destip="172.18.117.0/24"
    data={
        "id":1,
        "Temp":30,
        "Humi":50,
        "pressure":1000
    }

    payload=json.dumps(data).encode("utf-8")

    packet=IP(dst=destip)/TCP(dport=5000, sport=4000, flags="PA")/Raw(load=payload)

    packet.show()
    send(packet)

def Checker():
    def receivePacks(packet):
        if TCP in packet and Raw in packet:
            if packet[TCP].dport==5000:
                print("Packet Received")
                payload=packet[Raw].load
                data=json.loads(payload.decode("utf-8"))
                print(data)
    def sniffer():
        sniff(filter="tcp dport 5000", prn=receivePacks, store=False, timeout=30)

def dbInit(pipe):
    col.insert_one(pipe)
    count=col.count_documents({})
    if count>15:
        old=col.find_one({},sort=[("timestamp",1)])
        if old:
            col.delete_one({"_id":old["_id"]})

def SocketServer():
    HOST="0.0.0.0"
    PORT=5000
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((HOST,PORT))
    server.listen(5)
    print("Server is Running Listening on port 5000")
    conn, addr=server.accept()
    buffer=""
    print(f"Connection established with {addr}")
    while True:
        data=conn.recv(1024)
        if not data:
            print("Connection Terminated")
            break
        buffer+=data.decode("utf-8")
        # print(str)
        while "\n" in buffer:
            dataline,buffer=buffer.split("\n",1)
            if dataline:
                jsondata=json.loads(dataline)
                print("Data Received :",jsondata)
                dbInit(jsondata)
                print("Pushed To db")

    server.close()
    conn.close()


# def SocketClient():
#     HOST = '172.23.49.195'  
#     PORT = 6000       
#     client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     client.connect((HOST, PORT))
#     data = client.recv(1024).decode('utf-8')
#     print(f"Received from Server laptop: {data}")
#     client.close()

SocketServer()

# url="mongodb://localhost:27017/"
# client=pymongo.MongoClient(url)
# db=client["NASA"]
# col=db["astronauts"]

# n=int(input("Enter the employee id: "))
# res=col.find({"_id":n})
# print(res[0])