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

def executeCommand(path: str, args = [], errormsg = "") -> ProcessOutput:
    tlock.acquire()
    command = []
    command.append(path)
    for x in args:
        command.append(x)
    print("Executing " + path + " with args: " + " ".join(args))
    try:
        global exitcode
        global output
        #process = Popen(path + (' ' + args if args != "" else ""), stdout=PIPE)
        process = Popen(command, stdout=PIPE)
        (output, err) = process.communicate()
        exitcode = process.wait()
    except ValueError as err2:
        exitcode = -1
        print("[PYTHON ERROR] - " + err2.decode("utf-8"))
    finally:
        tlock.release()
    if(exitcode != 0):
        if (errormsg != ""):
            bot.send_message(CHAT_ID, errormsg)
        print("Executing command: ",end='')
        for part in command:
            print('|' + part + '|', end=' ')
        print()
        print("Generated this error:" + output.decode("utf-8"))
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

    def live(self, message: Message):
        if(AuthCheck(message.chat.id)):
            bot.send_message(message.chat.id, "Safe and Sound")
    def redocker(self, message: Message):
        if(AuthCheck(message.chat.id)):
            containerlistprc = executeCommand("docker", ["ps", "-a", "-q"], "Unable to get container list")
            if not containerlistprc.good:
                return
            containerlist = containerlistprc.output.splitlines()
            print(containerlist)
            restarted = True
            for container in containerlist:
                restarted = restarted & executeCommand("docker", ["restart", container], "Unable to restart" + container).good
            bot.send_message(message.chat.id, "All containers restarted" if restarted else "Not all container were restarted")
    
    def showsvc(self, message: Message):
        if(AuthCheck(message.chat.id)):
            processOut = executeCommand("docker", ["ps", "--format", "{{.Names}} -> {{.Status}}"], "Unable to access docker containers")
            if processOut.good:
                bot.send_message(message.chat.id, processOut.output)

bot.start()
bot.add_commands(Commands(bot))
while True:
    sleep(1)
