from scapy.all import TCP,IP,sniff,Raw
import json

def receive_packs(packets):
    if TCP in packets and Raw in packets:
        if(packets[TCP].dport==5000):
            try:
                payload=packets[Raw].load
                data=json.loads(payload.decode("utf-8"))

                print("Receiving data")
                print(data)

            except Exception as e:
                print(e)
print("Waiting for packets....")
a=sniff(filter="tcp port 5000",prn=receive_packs,store=True,timeout=30)
