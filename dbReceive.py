import socket
import json
import pymongo
from datetime import datetime, timezone

HOST = "0.0.0.0"  # Listen on all local interfaces
PORT = 5000

# Connect to local MongoDB instance
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["NASA"]
col = db["astronauts"]
MAX_DOCUMENTS = 16


def timestamp_as_utc(value):
    """Convert an ISO-8601 timestamp or Unix timestamp to a MongoDB Date."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        value = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    raise ValueError("timestamp must be an ISO-8601 string, Unix timestamp, or datetime")


def prepare_existing_timestamps():
    """Give pre-existing records the same sortable timestamp field."""
    for item in col.find({"timestamp_sort": {"$exists": False}}, {"timestamp": 1}):
        try:
            sortable_timestamp = timestamp_as_utc(item["timestamp"])
        except (KeyError, TypeError, ValueError, OverflowError):
            sortable_timestamp = datetime(1970, 1, 1, tzinfo=timezone.utc)
        col.update_one({"_id": item["_id"]}, {"$set": {"timestamp_sort": sortable_timestamp}})


def trim_collection():
    """Delete the oldest documents until the collection contains 16 records."""
    excess = col.count_documents({}) - MAX_DOCUMENTS
    if excess > 0:
        oldest_ids = [
            item["_id"]
            for item in col.find({}, {"_id": 1}).sort(
                [("timestamp_sort", pymongo.ASCENDING), ("_id", pymongo.ASCENDING)]
            ).limit(excess)
        ]
        if oldest_ids:
            deleted = col.delete_many({"_id": {"$in": oldest_ids}}).deleted_count
            print(f"[DB] Deleted {deleted} oldest document(s); {MAX_DOCUMENTS} retained.")


def insert_and_trim(document):
    if "timestamp" not in document:
        raise ValueError("Received document does not contain a timestamp")

    # Keep a normalized Date solely for ordering. String timestamps can have
    # different formats/time zones and are not reliably sortable as strings.
    document["timestamp_sort"] = timestamp_as_utc(document["timestamp"])
    result = col.insert_one(document)
    prepare_existing_timestamps()
    trim_collection()
    current_count = col.count_documents({})
    print(f"[DB] Collection now contains {current_count} document(s).")

    return result

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"[*] MongoDB TCP Bridge listening on port {PORT}...")
prepare_existing_timestamps()
trim_collection()

try:
    while True:
        client_sock, addr = server.accept()
        print(f"[+] Base station connected from {addr[0]}:{addr[1]}")
        
        buffer = ""
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                
                try:
                    json_doc = json.loads(line)
                    result = insert_and_trim(json_doc)
                    print(f"[OK] Inserted Doc ID: {result.inserted_id} | Dust: {json_doc.get('dust')} | Temp: {json_doc.get('temperature_c')}C")
                except json.JSONDecodeError as err:
                    print(f"[!] JSON parsing error: {err}")
                except Exception as err:
                    print(f"[!] Database insert error: {err}")
                    
        print(f"[-] Base station disconnected from {addr[0]}")
        client_sock.close()
except KeyboardInterrupt:
    print("\nShutting down bridge server...")
finally:
    server.close()
