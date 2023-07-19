import win32pipe, win32file, win32api, pywintypes
import sys
import json
import subprocess
from pyinjector import inject
import gfrequests
import psutil

# You need to put your path to NostaleClientX.exe here
NOSTALE_PATH = r"NostaleClientX.exe"
COUNTRY_CODE= "0"

def prepareResponse(request, response):
    resp = {}
    resp["id"] = request["id"]
    resp["jsonrpc"] = request["jsonrpc"]
    resp["result"] = response
    
    return json.dumps(resp, separators=(',', ':'))

def get_pid():
    last_started_pid = None
    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        if proc.info['name'] == "NostaleClientX.exe":
            if last_started_pid is None or proc.info['create_time'] > psutil.Process(last_started_pid).create_time():
                last_started_pid = proc.info['pid']
    return last_started_pid

def startGame(authCode, displayName):
    pipeName = r"\\.\pipe\GameforgeClientJSONRPC"
    subprocess.Popen([NOSTALE_PATH, "gf", COUNTRY_CODE]) #Launch NosTale with gf parameter

    exitAfterWrite = False
    
    while not exitAfterWrite:
        pipe = win32pipe.CreateNamedPipe(pipeName, win32pipe.PIPE_ACCESS_DUPLEX, win32pipe.PIPE_WAIT | win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE, 255, 0, 0, 3000, None) #Create pipe every time after write
        win32pipe.ConnectNamedPipe(pipe, None)

        code, resp = win32file.ReadFile(pipe, 1024)
        decoded = resp.decode(sys.stdout.encoding)
        data = json.loads(decoded)

        output = ""
        if data["method"] == "ClientLibrary.isClientRunning":
            output = prepareResponse(data, True)

        elif data["method"] == "ClientLibrary.initSession":
            output = prepareResponse(data, data["params"]["sessionId"])

        elif data["method"] == "ClientLibrary.queryAuthorizationCode":
            output = prepareResponse(data, authCode)

        elif data["method"] == "ClientLibrary.queryGameAccountName":
            output = prepareResponse(data, displayName)
            exitAfterWrite = True

        if output:
            win32file.WriteFile(pipe, output.encode(sys.stdout.encoding))

        if exitAfterWrite:
            break


    pid = get_pid()
    if pid is not None:
        #print(f"Process ID: {pid}")
        pass
    else:
        print("Process not found, exitting program...")
        exit()

    dll_path = "NostaleLogin.dll"
    inject(pid, dll_path)
    return pid

def selectAccount(account, token):
    uid, displayName = account

    authCode = gfrequests.getCode(uid, token, True)

    if not authCode:
        print("Couldn't get authCode!")
        return
        
    pid = startGame(authCode, displayName)
    return pid