import requests
import binascii
import hashlib
import uuid
import blackbox
import json
import winreg
import random
import os
import settings
from requests.auth import HTTPProxyAuth
import urllib3
import webbrowser
from urllib.parse import urlparse, parse_qs


os.environ["_TNT_CLIENT_APPLICATION_ID"] = "d3b2a0c1-f0d0-4888-ae0b-1c5e1febdafb"
os.environ["_TNT_SESSION_ID"] =  "12345678-1234-1234-1234-123456789012"

class NTLauncher:
    installation_id = "31262457-b31f-4c57-ac86-bb78b0b2f6e7"
    chrome_version = ""
    gameforge_version = ""
    username = settings.loginDetails.username
    password = settings.loginDetails.password
    locale = settings.loginDetails.locale
    cert = ""
    token = ""
    
def init_gf_version():
    response = requests.get("http://dl.tnt.gameforge.com/tnt/final-ms3/clientversioninfo.json")
    if response.status_code != 200:
        return

    json_response = json.loads(response.text)
    NTLauncher.chrome_version = "C" + json_response["version"]
    NTLauncher.gameforge_version = json_response["minimumVersionForDelayedUpdate"]

def init_installation_id():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Gameforge4d\\GameforgeClient\\MainApp") as key:
            NTLauncher.installation_id = winreg.QueryValueEx(key, "InstallationId")[0]
    except OSError:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Gameforge4d\\GameforgeClient\\MainApp") as key:
                NTLauncher.installation_id = winreg.QueryValueEx(key, "InstallationId")[0]
        except OSError:
            return
      
def init_cert():
    try:
        with open("new_cert.pem", "r") as file:
            data = file.read()
    except IOError as e:
        print("Error opening cert file:", str(e))
        return

    start = data.find("-----BEGIN CERTIFICATE-----")
    end = data.find("-----END CERTIFICATE-----", start)

    if start == -1 or end == -1:
        print("Invalid certificate format")
        return

    NTLauncher.cert = data[start + len("-----BEGIN CERTIFICATE-----") : end]

def auth():
    init_gf_version()
    init_installation_id()
    init_cert()
    URL = "https://spark.gameforge.com/api/v1/auth/sessions"
    HEADERS = {
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "TNT-Installation-Id" : NTLauncher.installation_id,
        "Origin" : "spark://www.gameforge.com",
    }

    CONTENT = {
        "blackbox" : blackbox.updateBlackbox(),
        "email" : NTLauncher.username,
        "locale" : NTLauncher.locale,
        "password" : NTLauncher.password,
    }

    r = requests.post(URL, headers=HEADERS, json=CONTENT)

    if r.status_code != 201:
        print("failed (probably blackbox)")
        return 0
        
    response = r.json()
    token = response["token"]
    NTLauncher.token = token
    return token

def getAccounts(token):

    URL = "https://spark.gameforge.com/api/v1/user/accounts"

    HEADERS = {
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "TNT-Installation-Id" : NTLauncher.installation_id,
        "Origin" : "spark://www.gameforge.com",
        "Authorization" : "Bearer {}".format(token),
        "Connection" : "Keep-Alive"
    }
    r = requests.get(URL, headers=HEADERS)

    accounts = []
    response = r.json()

    for key in response.keys():
        accounts.append((key, response[key]["displayName"]))
        
    return(accounts)

def getFirstNumber(uuid):
        for char in uuid:
            if char.isdigit():
                return char
        
        return None
    
def generateThirdTypeUserAgentMagic(account_id):
    firstLetter = getFirstNumber(NTLauncher.installation_id)
    firstTwoLettersOfAccountId = account_id[:2]
    
    if firstLetter == None or int(firstLetter) % 2 == 0:
        hashOfCert = hashlib.sha1(NTLauncher.cert.encode()).hexdigest()
        hashOfVersion = hashlib.sha1(NTLauncher.chrome_version.encode("ascii")).hexdigest()
        hashOfInstallationId = hashlib.sha256(NTLauncher.installation_id.encode("ascii")).hexdigest()
        hashOfAccountId = hashlib.sha1(account_id.encode("ascii")).hexdigest()
        hashOfSum = hashlib.sha256((hashOfCert + hashOfVersion + hashOfInstallationId + hashOfAccountId).encode("ascii")).hexdigest()
        return firstTwoLettersOfAccountId + hashOfSum[:8]
        
    else:
        hashOfCert = hashlib.sha1(NTLauncher.cert.encode()).hexdigest()
        hashOfVersion = hashlib.sha256(NTLauncher.chrome_version.encode("ascii")).hexdigest()
        hashOfInstallationId = hashlib.sha1(NTLauncher.installation_id.encode("ascii")).hexdigest()
        hashOfAccountId = hashlib.sha256(account_id.encode("ascii")).hexdigest()
        hashOfSum = hashlib.sha256((hashOfCert + hashOfVersion + hashOfInstallationId + hashOfAccountId).encode("ascii")).hexdigest()
        return firstTwoLettersOfAccountId + hashOfSum[-8:]
    
def send_iovation(account_id):
    content = {}
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "TNT-Installation-Id": NTLauncher.installation_id,
        "Origin": "spark://www.gameforge.com",
        "Connection": "Keep-Alive",
        "Authorization" : "Bearer {}".format(NTLauncher.token)
    }

    content["accountId"] = account_id
    content["blackbox"] = blackbox.updateBlackbox(),
    content["type"] = "play_now"

    response = requests.post("https://spark.gameforge.com/api/v1/auth/iovation", headers=headers, data=json.dumps(content))

    if response.status_code != 200:
        return False

    json_response = response.json()

    if json_response["status"] != "ok":
        return False

    return True

def convertToken(guid):
    return binascii.hexlify(guid.encode()).decode()

def getCode(account_id, token, raw=False):
    content = {}
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Chrome/" + NTLauncher.chrome_version + " (" + generateThirdTypeUserAgentMagic(account_id) + ")",
        "Authorization" : "Bearer {}".format(token),
        "Connection": "Keep-Alive",
        "tnt-installation-id": NTLauncher.installation_id
    }

    if token == "":
        return ""

    if not send_iovation(account_id):
        return ""

    gsid = str(uuid.uuid4()) + "-" + str(random.randint(1000, 9999))

    content["platformGameAccountId"] = account_id
    content["gsid"] = gsid
    content["blackbox"] = blackbox.updateBlackbox(),
    content["gameId"] = "dd4e22d6-00d1-44b9-8126-d8b40e0cd7c9"

    r = requests.post("https://spark.gameforge.com/api/v1/auth/thin/codes", headers=headers, data=json.dumps(content))

    if r.status_code != 201:
        return False

    if raw:
        return r.json()["code"]
    
    return convertToken(r.json()["code"])