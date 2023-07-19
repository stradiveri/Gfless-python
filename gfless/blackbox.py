import base64
import json
from urllib.parse import unquote
from urllib.parse import quote
from datetime import datetime
import requests
from random import randint

BLACKBOX_FIELDS = ["v", "tz", "dnt", "product", "osType", "app", "vendor", "mem", "con", "lang", "plugins", "gpu", "fonts", "audioC", "width", "height", "depth", "lStore", "sStore", "video", "audio", "media", "permissions", "audioFP", "webglFP", "canvasFP", "creation", "uuid", "d", "osVersion", "vector", "userAgent", "serverTimeInMS", "request"]

def decode(blackbox):
    decoded_blackbox = blackbox.replace("tra:", "").replace("_", "/").replace("-", "+")
    decoded_blackbox = base64.b64decode(decoded_blackbox + '=' * (-len(decoded_blackbox) % 4))

    uri_decoded = bytearray()
    uri_decoded.append(decoded_blackbox[0])

    for i in range(1, len(decoded_blackbox)):
        b = decoded_blackbox[i - 1]
        a = decoded_blackbox[i]

        if a < b:
            a += 0x100

        c = (a - b).to_bytes(1, "big")
        uri_decoded.extend(c)

    fingerprint_str = unquote(uri_decoded.decode("utf-8"))
    fingerprint_array = json.loads(fingerprint_str)
    fingerprint = {}

    if len(fingerprint_array) != len(BLACKBOX_FIELDS):
        print("BlackBox::decode Error size doesn't match")
        return bytearray()

    for i in range(len(BLACKBOX_FIELDS)):
        fingerprint[BLACKBOX_FIELDS[i]] = fingerprint_array[i]

    return fingerprint

def format_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def encode_blackbox(fingerprint):
    fingerprint_array = []

    for field in BLACKBOX_FIELDS:
        fingerprint_array.append(fingerprint[field])

    fingerprint_array_str = json.dumps(fingerprint_array, separators=(",", ":"))
    uri_encoded = quote(fingerprint_array_str, safe="-_!~*.'()")

    blackbox = bytearray()
    blackbox.append(ord(uri_encoded[0]))

    for i in range(1, len(uri_encoded)):
        a = blackbox[i - 1]
        b = ord(uri_encoded[i])
        c = (a + b) % 256
        blackbox.append(c)

    blackbox = base64.b64encode(blackbox).decode("utf-8")
    blackbox = blackbox.replace("/", "_").replace("+", "-").rstrip("=")

    return "tra:" + blackbox

def updateCreation(fingerprint):
    fingerprint["creation"] = datetime.utcnow().isoformat(timespec='milliseconds')+"Z"
    
def updateServerTime(fingerprint):
    response = requests.head("https://gameforge.com/tra/game1.js")
    date = response.headers.get("Date")
    date = date.replace("GMT", "UTC")
    dateTime = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
    fingerprint["serverTimeInMS"] = dateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def updateTimings(fingerprint):
    fingerprint["d"] = randint(10, 300)

def updateVector(fingerprint):
    content = base64.b64decode(fingerprint["vector"].encode("latin1"))
    content = content[:content.rfind(b" ")]
    content = content[1:] + bytes([randint(32, 126)])
    
    newVector = content + b" " + str(int(datetime.now().timestamp() * 1000)).encode("utf-8")
    fingerprint["vector"] = base64.b64encode(newVector).decode()
    
def updateBlackbox():
    file_path = "identity.json"
   
    with open(file_path, "r") as file:
        fingerprint = json.load(file)
    updateServerTime(fingerprint)
    updateCreation(fingerprint)
    updateTimings(fingerprint)
    updateVector(fingerprint)
    blackbox = encode_blackbox(fingerprint)
    return blackbox
    
