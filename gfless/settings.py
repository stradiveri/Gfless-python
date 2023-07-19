import configparser

settings = configparser.ConfigParser()
settings.read("setup.ini",encoding='utf-8')


class accounts:
    listOfAccounts = settings["accounts"]["listOfAccounts"]
    
class loginDetails:
    username = settings["login"]["username"]
    password = settings["login"]["password"]
    locale = settings["login"]["locale"]