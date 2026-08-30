import socket
import pymongo 
import json
import random
import time
from datetime import datetime,timezone

HOST="172.23.49.195"
PORT=5000
client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST,PORT))

for i in range(20):
    message={
        "_id": i,
        "gas":random.randint(0,500),
        "temp":random.randint(0,500),
        "humid":random.randint(0,100),
    }
    message["timestamp"] = str(datetime.now(timezone.utc))
    strng=json.dumps(message) + "\n"
    print(type(strng))
    client.sendall(strng.encode("utf-8"))
    print("Message Sent")
    time.sleep(1)
client.close()


# c=pymongo.MongoClient("mongodb://localhost:27017/")
# db=c["SIH"]
# col=db["data"]
# json_data=json.loads(data)
# for key,value in json_data.items():
#     print(f"{key}: {value}")
# col.insert_one(json_data)