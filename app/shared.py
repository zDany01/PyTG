from threading import Lock
from origamibot import OrigamiBot
from config import BOT_TOKEN

botInstance: OrigamiBot = OrigamiBot(BOT_TOKEN)
threadLock: Lock = Lock()
print("Shared bot instance initialized")