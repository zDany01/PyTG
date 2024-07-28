from threading import Lock
from os.path import exists, getmtime
from time import sleep, strftime, localtime
from typing import Iterator, Literal
from math import trunc
from origamibot import OrigamiBot as Bot
from subprocess import Popen, PIPE
from origamibot.core.teletypes import *
from re import *

BOT_TOKEN = "6703837324:AAELx1nu80hppsgprzDdSPHZXMCMm8WWcNw"
CHAT_ID = 1323764255
MSG_LIMIT = 60
bot = Bot(BOT_TOKEN)
tlock = Lock()

class ProcessOutput:
    def __init__(self, exitcode: int, output: str):
        self.ecode = exitcode
        self.output = output
        self.good = exitcode == 0

class CodeMessage:
    def __init__(self, caption: str, message = ""):
        self.caption = caption
        self.message = message

    def append(self, text: str):
        self.message += text
        return self
    
    def create(self, chatID: int):
        self.messageObject = bot.send_message(chatID, "```{0}\n{1}```".format(self.caption, self.message), "MarkdownV2")
    
    def send(self):
        self.messageObject = bot.edit_message_text(self.messageObject.chat.id, "```{0}\n{1}```".format(self.caption, self.message), self.messageObject.message_id, parse_mode="MarkdownV2")
    
    def clear(self):
        self.message = ""

def AuthCheck(chat_id: int) -> bool:
    if(chat_id != CHAT_ID):
        bot.send_message(chat_id, "You are not authorized.")
        return False
    return True

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
            sendMsg(CHAT_ID, errormsg)

        print("Executing command: ",end='')
        for part in command:
            print('|' + part + '|', end=' ')
        print()       
        print("Generated this error:" + output.decode("utf-8"))
        return ProcessOutput(exitcode, output.decode("utf-8"))
    return ProcessOutput(exitcode, output.decode("utf-8"))

def getContainers(onlyActive: bool = False) -> list[str]:
    containerlistprc = executeCommand("docker", ["ps", "-a", "-q"] if not onlyActive else ["ps", "-q"], "Unable to get container list")
    if not containerlistprc.good:
        return
    return containerlistprc.output.splitlines()

def getContainersData(Containers: Literal["ALL", "ACTIVE"] = "ACTIVE", formatString: str = "") -> str:
        return executeCommand("docker", ["ps", "-a", "--format", formatString] if Containers == "ALL" else ["ps", "--format", formatString]).output

def getContainerData(CtID: str, formatString: str = None) -> str:
    return executeCommand("docker", ["ps", "-a", "--filter", "id=" + CtID, "--format", formatString] if formatString is not None else ["ps", "-a", "--filter", "id=" + CtID], "Unable to get container data for CtID: " + CtID).output.strip()

def getContainerDataList(CtIDs: list[str], formatString: str = None) -> list[str]:
    dataList: list[str] = []
    for CtID in CtIDs:
        dataList.append(getContainerData(CtID, formatString))
    return dataList

def startContainer(CtID: str, startOnly: bool = True, errormsg: str = "") -> int:
    """
    :param errormsg: this message will be displayed if there is an error when executing the start/restart command NOT if the container is already started
    :return 0: if started correctly
    :return 1: if already started
    :return 2: if restarted correctly
    :return -1: if an error occured during starting/restarting
    """
    if(getContainerData(CtID, "{{.Status}}").startswith("Up")):
        if (startOnly):
            return 1
        return 2 if executeCommand("docker", ["restart", CtID], errormsg).good else -1
    return 0 if executeCommand("docker", ["start", CtID], errormsg).good else -1

def startContainers(CtIDs: list[str], startOnly: bool = True) -> list[int]:
    startResult: list[int] = []
    for CtID in CtIDs:
        startResult.append(startContainer(CtID, startOnly))
    return startResult

def stopContainer(CtID: str, errormsg = "") -> int:
    """
    :param errormsg: this message will be displayed if there is an error when executing the stop command NOT if the container is already stopped
    :return 0: if stopped correctly
    :return 1: if already stopped
    :return -1: if an error occured during stopping
    """
    if(getContainerData(CtID, "{{.Status}}").startswith("Exited")):
        return 1
    return 0 if executeCommand("docker", ["stop", CtID], errormsg).good else -1

def stopContainers(CtIDs: list[str]) -> list[int]:
    stopResults: list[int] = []
    for CtID in CtIDs:
        stopResults.append(stopContainer(CtID))
    return stopResults

def sendMsg(chatID: int, message: str) -> Message:
    return bot.send_message(chatID, "<b>PyBot</b>\n" + message, "HTML")

def editMsg(message: Message, content: str, append: bool = False, parsemode = "HTML"):
    return bot.edit_message_text(message.chat.id, message.text + content if append else "<b>PyBot</b>\n" + content, message.message_id, parse_mode=parsemode)

def appendRemaining(str: str, c: str, maxLength: int) -> str:
    for _ in range(maxLength-len(str)):
        str += c
    return str


class Commands:
    rflag = False
    def __init__(self, bot: Bot):
        self.bot = bot

    def backup(self, message: Message):
        if(AuthCheck(message.chat.id)):
            executeCommand("/home/danyb/iSSD/Backup/backup", ["--manual"], "Error during system backup")
                    
    def updatedb(self, message: Message):
        if(AuthCheck(message.chat.id)):
            executeCommand("/home/danyb/iSSD/AutoJobs/updateDB", errormsg= "Error while updating nginx IP database")

    def restart(self, message: Message):
        if(AuthCheck(message.chat.id)):
            if(self.rflag):
                sendMsg(message.chat.id, "Rebooting system...")
                self.rflag = False
                executeCommand("reboot")
            else:
               sendMsg(message.chat.id, "Are you sure? /yes | /no")

    def yes(self, message: Message):
        if(AuthCheck(message.chat.id)):
            self.rflag = True
            self.restart(message)

    def no(self, message: Message):
        if(AuthCheck(message.chat.id)):
            self.rflag = False
            sendMsg(message.chat.id, "Operation aborted")

    def ping(self, message: Message):
        if(AuthCheck(message.chat.id)):
            bot.send_message(message.chat.id, "Pong")

    def redocker(self, message: Message):
        if(AuthCheck(message.chat.id)):
            containerlist = getContainers(True)
            progressMessage = CodeMessage("PyDocker", "Restarting active containers..")
            progressMessage.create(message.chat.id)
            successNumber = 0
            for container in containerlist:
                containerName: str = getContainerData(container, "{{.Names}}")
                progressMessage.append('\n' + containerName).send()
                offset = ""
                for _ in range(1, MSG_LIMIT - len(containerName)):
                    offset += ' '
                if startContainer(container, False, "Unable to restart" + container) == 2:
                    progressMessage.append(offset + "✅").send()
                    successNumber += 1
                else:
                    progressMessage.append(offset + "❌").send()
            sendMsg(message.chat.id, "Restarted {0} of {1} active containers".format(successNumber, len(containerlist)))
    
    def showsvc(self, message: Message):
        if(AuthCheck(message.chat.id)):
            filteredCDatas: Iterator[Match[str]] = finditer("(?P<ContainerName>[\w-]+) -> (?P<ContainerStatus>\w+)(?: \(\d+\))? (?P<Time>.+)", getContainersData("ALL", "{{.Names}} -> {{.Status}}"))
            wordOffset = trunc(MSG_LIMIT/3)
            serviceStatus: CodeMessage = CodeMessage("PyDocker", appendRemaining("Container Name", ' ', wordOffset) + appendRemaining("Status", ' ', wordOffset) + appendRemaining("Time", ' ', wordOffset) + '\n')
            serviceStatus.create(message.chat.id)
            for ctData in filteredCDatas:
                for i in range(1,4):
                    serviceStatus.append(appendRemaining(ctData.group(i), ' ', wordOffset))
                serviceStatus.append('\n').send()
                
    def lastbackup(self, message: Message):
        if(AuthCheck(message.chat.id)):
            updatePath = "/home/danyb/iSSD/Backup/update"
            if not exists(updatePath):
                sendMsg(message.chat.id, "Unable to get last backup date\nMake sure that a backup has been done before")
                return
            sendMsg(message.chat.id, strftime("The latest backup was done on <i>%b %-d, %Y - %I:%M:%S %p</i>", localtime(getmtime(updatePath))))

bot.start()
bot.add_commands(Commands(bot))
while True:
    sleep(1)
