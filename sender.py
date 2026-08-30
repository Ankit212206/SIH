import json
from scapy.all import TCP,IP,sniff,send,Raw
import random
import time
destip="172.18.117.0/24"
start=time.time()
packet_id=1
while time.time() - start < 10:
    data={
        "id":packet_id,
        "Temp":random.randint(25, 40),
        "Humi":random.randint(20, 60),
        "pressure":random.randint(800, 1300)
    }    
    payload=json.dumps(data).encode("utf-8")

    packet=IP(dst=destip)/TCP(dport=5000, sport=4000)/Raw(load=payload)
    packet.show()
    send(packet, verbose=False)
    print(f"Sent Packet ID: {packet_id}")
    packet_id+=1
    time.sleep(1)