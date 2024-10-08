from threading import Timer
from time import sleep
from os import _exit as killProcess
from os.path import exists, dirname, abspath
import requests
try:
    import config
except:
    print("You need to rename \"config.py.template\" to \"config.py\"" if exists(dirname(abspath(__file__)) + "/config.py.template") else "No configuration file found...\nExiting...")
    exit(1)
from shared import botInstance as bot
from commands import Commands
from callback_actions import CallbackActions

def heartbeat(retries: int = 0):
    if retries > config.HEARTBEAT_MAX_RETRIES:
        print("[HEARTBEAT] Reached max tries, disabling HEARTBEAT")
        if config.HEARTBEAT_FAIL_ON_ERROR:
            print("[HEARTBEAT] Detected fail on error, closing now..")
            killProcess(1)
        return

    try:
        requests.head(config.HEARTBEAT_URL)
        if config.HEARTBEAT_LOG_SUCCESS:
            print("[HEARTBEAT] Ok")
        Timer(config.HEARTBEAT_INTERVAL, heartbeat).start()
    except:
        print("[HEARTBEAT] Unable to reach " + config.HEARTBEAT_URL)
        Timer(config.HEARTBEAT_INTERVAL, heartbeat, [retries + 1]).start()

if (config.HEARTBEAT_ENABLED):
    Timer(5, heartbeat).start()

bot.start()
bot.add_commands(Commands())
bot.add_callback(CallbackActions())
while True:
    sleep(1)
