import os
import sys
# Add the current directory to the Python module search path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import gfrequests
import client
import settings
import time

if __name__ == "__main__":
    pids = []
    
    selectedAccounts = settings.accounts.listOfAccounts.split(",")
    token = gfrequests.auth()
    
    if token == 0:
        print("Couldn't auth!")
        exit()
    else:
        print(str(time.strftime('[%H:%M:%S]'))+" Logged In succesfully !")

    accounts = gfrequests.getAccounts(token)
    if len(accounts) == 0:
        print("You don't have any any account")

    for acc in selectedAccounts:
        for i in range(len(accounts)):
            if accounts[i][1] == acc:
                pid = client.selectAccount(accounts[i], token)
                print(str(time.strftime('[%H:%M:%S]'))+" Starting:",acc)
                time.sleep(12)
                pids.append(pid)

    print(pids)
