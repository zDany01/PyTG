from threading import Lock
from origamibot import OrigamiBot
from scriptmanager import ScriptManager
from config import BOT_TOKEN, SCRIPTS_DIRECTORY_PATH

botInstance: OrigamiBot = OrigamiBot(BOT_TOKEN)
scriptManager: ScriptManager = ScriptManager(SCRIPTS_DIRECTORY_PATH)
threadLock: Lock = Lock()
print("Shared bot instance initialized")