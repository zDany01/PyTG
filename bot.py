from os import system
from threading import Lock
from time import sleep
from origamibot import OrigamiBot as Bot
from subprocess import Popen, PIPE
from origamibot.core.teletypes import *

BOT_TOKEN = "6703837324:AAELx1nu80hppsgprzDdSPHZXMCMm8WWcNw"
CHAT_ID = 1323764255
bot = Bot(BOT_TOKEN)
tlock = Lock()

class ProcessOutput:
    def __init__(self, exitcode: int, output: str):
        self.ecode = exitcode
        self.output = output
        self.good = exitcode == 0

def executeCommand(path: str, args: str = "", errormsg = "") -> ProcessOutput:
    tlock.acquire()
    try:
        global exitcode
        global output
        process = Popen(path + (' ' + args if args != "" else ""), stdout=PIPE)
        (output, err) = process.communicate()
        exitcode = process.wait()
    except:
        exitcode = -1
    finally:
        tlock.release()
    if(exitcode != 0):
        if (errormsg != ""):
            bot.send_message(CHAT_ID, errormsg)
        return ProcessOutput(exitcode, output.decode("utf-8"))
    return ProcessOutput(exitcode, output.decode("utf-8"))

def AuthCheck(chat_id: int) -> bool:
    if(chat_id != CHAT_ID):
        bot.send_message(chat_id, "You are not authorized.")
        return False
    return True

class Commands:
    rflag = False
    def __init__(self, bot: Bot):
        self.bot = bot

    def backup(self, message: Message):
        if(AuthCheck(message.chat.id)):
            executeCommand("/home/danyb/iSSD/Backup/backup", "", "Error during system backup")
                
    
    def updatedb(self, message: Message):
        if(AuthCheck(message.chat.id)):
            executeCommand("/home/danyb/iSSD/AutoJobs/updateDB", "", "Error while updating nginx IP database")

    def restart(self, message: Message):
        if(AuthCheck(message.chat.id)):
            if(self.rflag):
                bot.send_message(message.chat.id, "Rebooting system...")
                self.rflag = False
                executeCommand("reboot")
            else:
               bot.send_message(message.chat.id, "Are you sure? /yes | /no")

    def yes(self, message: Message):
        if(AuthCheck(message.chat.id)):
            self.rflag = True
            self.restart(message)

    def no(self, message: Message):
        if(AuthCheck(message.chat.id)):
            self.rflag = False
            bot.send_message(message.chat.id, "Operation aborted.")

    #def redocker(self, message: Message):
    #    if(AuthCheck(message.chat.id)):
    #        if(executeCommand("bash", "-c \"docker restart $(docker ps -a -q)\"", "Unable to restart docker containers..").good):
    #            bot.send_message(message.chat.id, "All containers successfully restarted")
    #
    #def showsvc(self, message: Message):
    #    if(AuthCheck(message.chat.id)):
    #        processOut = executeCommand("bash", "-c \"docker ps --format \"{{{{.Names}}}} -> {{{{.Status}}}}\"", "Unable to access docker containers")
    #        if processOut.good:
    #            bot.send_message(message.chat.id, processOut.output)

bot.start()
bot.add_commands(Commands(bot))
while True:
    sleep(1)