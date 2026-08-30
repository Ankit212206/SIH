import json
import serial
import pymongo
from datetime import datetime,timezone

url="mongodb://localhost:27017/"
client=pymongo.MongoClient(url)
db=client["NASA"]
col=db["astronauts"]

def dbInit(pipe):
    pipe["timestamp"]=str(datetime.now(timezone.utc))
    col.insert_one(pipe)
    count=col.count_documents({})
    if count>15:
        old=col.find_one({},sort=[("timestamp",1)])
        if old:
            col.delete_one({"_id":old["_id"]})
ser = serial.Serial("COM5", 115200, timeout=1)
print("[*] Listening on USB Serial...")

while True:
  line = ser.readline().decode("utf-8").strip()
  if line.startswith("{"):
    try:
      jsondata = json.loads(line)
      print("Data Received via USB:", jsondata)
      dbInit(jsondata)
    except Exception as e:
      print("Parse error:", e)