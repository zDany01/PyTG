from threading import Lock
from os.path import exists, getmtime
from io import StringIO
from time import sleep, strftime, strptime, localtime
from typing import Iterator, Literal
from math import trunc
from origamibot import OrigamiBot as Bot
from origamibot.util import condition
from subprocess import Popen, PIPE
from origamibot.core.teletypes import *
from re import *

import config
bot = Bot(config.BOT_TOKEN)
tlock = Lock()

class ProcessOutput:
    def __init__(self, exitcode: int, output: str):
        self.ecode = exitcode
        self.output = output
        self.good = exitcode == 0

class CodeMessage:
    def __init__(self, caption: str, message: str = ""):
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
    if chat_id != config.CHAT_ID:
        bot.send_message(chat_id, "You are not authorized.")
        return False
    return True

def executeCommand(path: str, args: list[str | int | bool] = [], errormsg: str = "") -> ProcessOutput:
    tlock.acquire()
    command: list[str] = []
    command.append(path)
    for arg in args:
        command.append(arg)
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

    if exitcode != 0:
        if errormsg != "":
            sendMsg(config.CHAT_ID, errormsg)

        print("Executing command: ",end='')
        for part in command:
            print('|' + part + '|', end=' ')
        print()       
        print("Generated this error:" + output.decode("utf-8"))
        return ProcessOutput(exitcode, output.decode("utf-8"))
    return ProcessOutput(exitcode, output.decode("utf-8"))

def getContainers(activeOnly: bool = False) -> list[str]:
    containerlistprc: ProcessOutput = executeCommand("docker", ["ps", "-a", "-q"] if not activeOnly else ["ps", "-q"], "Unable to get container list")
    return containerlistprc.output.splitlines() if containerlistprc.good else None

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
    if getContainerData(CtID, "{{.Status}}").startswith("Up"):
        if (startOnly):
            return 1
        return 2 if executeCommand("docker", ["restart", CtID], errormsg).good else -1
    return 0 if executeCommand("docker", ["start", CtID], errormsg).good else -1

def startContainers(CtIDs: list[str], startOnly: bool = True) -> list[int]:
    startResult: list[int] = []
    for CtID in CtIDs:
        startResult.append(startContainer(CtID, startOnly))
    return startResult

def stopContainer(CtID: str, errormsg: str = "") -> int:
    """
    :param errormsg: this message will be displayed if there is an error when executing the stop command NOT if the container is already stopped
    :return 0: if stopped correctly
    :return 1: if already stopped
    :return -1: if an error occured during stopping
    """
    if getContainerData(CtID, "{{.Status}}").startswith("Exited"):
        return 1
    return 0 if executeCommand("docker", ["stop", CtID], errormsg).good else -1

def stopContainers(CtIDs: list[str]) -> list[int]:
    stopResults: list[int] = []
    for CtID in CtIDs:
        stopResults.append(stopContainer(CtID))
    return stopResults

def sendMsg(chatID: int, message: str, replyMarkup: ReplyMarkup = None) -> Message:
    return bot.send_message(chatID, "<b>PyBot</b>\n" + message, "HTML", reply_markup=replyMarkup)

def editMsg(message: Message, content: str, append: bool = False, parsemode = "HTML", replyMarkup: ReplyMarkup | None = None) -> Message:
    return bot.edit_message_text(message.chat.id, message.text + content if append else "<b>PyBot</b>\n" + content, message.message_id, parse_mode=parsemode, reply_markup=replyMarkup)

def appendRemaining(str: str, c: str, maxLength: int) -> str:
    for _ in range(maxLength-len(str)):
        str += c
    return str

def createDockerSelectMenu(chatID: int | None, CtIDs: list[str], callbackSfx: str = "docker-", closingRow: list[InlineKeyboardButton] | None = None, messageHolder: Message | None = None) -> Message:
            messageMenu: list[list[InlineKeyboardButton]] = []
            containerNo: int = len(CtIDs)
            rowOffset: int = trunc(containerNo/2)
            for i in range(0, rowOffset):
                messageMenu.append([InlineKeyboardButton(getContainerData(CtIDs[i], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i]), InlineKeyboardButton(getContainerData(CtIDs[i+rowOffset], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i+rowOffset])])

            if rowOffset * 2 != containerNo:
                messageMenu.append([InlineKeyboardButton(getContainerData(CtIDs[-1], "{{.Names}}"), callback_data=callbackSfx + CtIDs[-1])]) #-1 obtain the last element of the list

            if closingRow is not None:
                messageMenu.append(closingRow)

            if messageHolder is None:
                return sendMsg(chatID, "Select a docker container", InlineKeyboardMarkup(messageMenu))
            else:
                return editMsg(messageHolder, "Select a docker container", replyMarkup=InlineKeyboardMarkup(messageMenu))

class CallbackAction:
    #CallBack -> Action
    # exit -> closes the docker selection menu
    # docker-[ID] -> create a container managment menu for that container ID
    # reopen -> recreate a docker selection menu
    # dstart-[ID] -> start a docker container
    # dstop-[ID] -> stop a docker container
    # drestart-[ID] -> restart a docker container
    # dlog-[ID] -> get last execution log of a docker container

    def logquery(self, cbQuery: CallbackQuery):
        print(f"Recived query: {cbQuery.data} from {cbQuery.from_user.username}")

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dstart-"))
    def dstart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstart-", "")
            bot.answer_callback_query(cbQuery.id, "Container started succesfully" if startContainer(CtID) == 0 else "Unable to start this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dstop-"))
    def dstop(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstop-", "")
            bot.answer_callback_query(cbQuery.id, "Container stopped succesfully" if stopContainer(CtID) == 0 else "Unable to stop this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("drestart-"))
    def drestart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("drestart-", "")
            bot.answer_callback_query(cbQuery.id, "Container restarted succesfully" if startContainer(CtID, False) == 2 else "Unable to restart this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dlog-"))
    def dlog(self, cbQuery: CallbackQuery):
        chatID: int = cbQuery.message.chat.id
        if AuthCheck(chatID):
            CtID: str = cbQuery.data.replace("dlog-", "")
            logCommand = executeCommand("docker", ["logs", CtID])
            if not logCommand.good:
                bot.answer_callback_query(cbQuery.id, "Unable to get container logs")
                return
            virtualFile: StringIO = StringIO()
            virtualFile.name = f'{getContainerData(CtID, "{{.Names}}")} ({strftime("%b %-d %Y %H-%M-%S", localtime())}).log'
            virtualFile.write(logCommand.output)
            virtualFile.flush()
            virtualFile.seek(0)
            bot.send_document(chatID, virtualFile)
            virtualFile.close()
            bot.answer_callback_query(cbQuery.id)

    @condition(lambda c, cbQuery: cbQuery.data == "exit")
    def closeMenu(self, cbQuery: CallbackQuery):
        menuMessage: Message = cbQuery.message
        if AuthCheck(menuMessage.chat.id):
            editMsg(menuMessage, "Menu closed")
        bot.answer_callback_query(cbQuery.id)

    @condition(lambda c, cbQuery, updateOnly=False: cbQuery.data.startswith("docker-") or updateOnly)
    def createMenu(self, cbQuery: CallbackQuery, updateOnly: bool | None = False):
        menuMessage: Message = cbQuery.message
        if AuthCheck(menuMessage.chat.id):
            CtID: str = cbQuery.data.replace("docker-", "")
            if CtID in getContainers():
                ctData: str = match("(?P<ContainerName>[\w-]+) -> (?P<ContainerStatus>\w+)(?: \(\d+\))? (?P<Time>.+)\[\d+.?\w+ \(virtual (?P<Size>.+)\)\]\/(?P<UpdTime>.+)", getContainerData(CtID, "{{.Names}} -> {{.Status}}[{{.Size}}]/{{.CreatedAt}}"))
                ctName: str = ctData.group("ContainerName")
                ctStatus: str = ctData.group("ContainerStatus")
                ctRunning: bool = ctStatus == "Up"
                ctUpTime: str = ctData.group("Time")
                ctSize: str = ctData.group("Size")
                ctLastUpd = strftime("<i>%b %-d, %Y - %I:%M %p</i>", strptime(ctData.group("UpdTime"), "%Y-%m-%d %H:%M:%S %z %Z"))

                buttons = []
                if ctRunning:
                    buttons.append([InlineKeyboardButton("Stop", callback_data=f"dstop-{CtID}")])
                    buttons.append([InlineKeyboardButton("Restart", callback_data=f"drestart-{CtID}")])
                else:
                    buttons.append([InlineKeyboardButton("Start", callback_data=f"dstart-{CtID}")])
                buttons.append([InlineKeyboardButton("Logs", callback_data=f"dlog-{CtID}")])
                buttons.append([InlineKeyboardButton("Back", callback_data="reopen")])

                editMsg(menuMessage, f"<b>{ctName.capitalize()}</b>\nStatus: <b>{ctStatus}</b>" + (f"\nRunning for {ctUpTime.lower()}" if ctRunning else f" ({ctUpTime})") + f"\nLast Updated: {ctLastUpd}\nImage Size: {ctSize}", replyMarkup=InlineKeyboardMarkup(buttons))
                if updateOnly:
                    return
                bot.answer_callback_query(cbQuery.id)
            else:
                print("Requested query on non-existent container - " + CtID)
                if updateOnly:
                    return
                bot.answer_callback_query(cbQuery.id, "The selected container does not exist")

    @condition(lambda c, cbQuery: cbQuery.data == "reopen")
    def reOpenMenu(self, cbQuery: CallbackQuery):
        menuMessage: Message = cbQuery.message
        if AuthCheck(menuMessage.chat.id):
            createDockerSelectMenu(None, getContainers(), closingRow=[InlineKeyboardButton("Close", callback_data="exit")], messageHolder=menuMessage)
            bot.answer_callback_query(cbQuery.id)

    @condition(lambda c, cbQuery: cbQuery.data == "ryes")
    def ryes(self, cbQuery: CallbackQuery):
        message: Message = cbQuery.message
        if AuthCheck(message.chat.id):
            bot.answer_callback_query(cbQuery.id, "Rebooting...")
            editMsg(message, "System Rebooted")
            executeCommand("reboot")

    @condition(lambda c, cbQuery: cbQuery.data == "rno")
    def rno(self, cbQuery:CallbackQuery):
        message: Message = cbQuery.message
        if AuthCheck(message.chat.id):
            editMsg(message, "Operation aborted.")
            bot.answer_callback_query(cbQuery.id)

class Commands:

    def backup(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.BACKUP_SCRIPT_PATH, config.BACKUP_SCRIPT_ARGS, "Error during system backup")
                    
    def updatedb(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.NGINX_DB_UPDATE_PATH, errormsg= "Error while updating nginx IP database")

    def reboot(self, message: Message):
        if AuthCheck(message.chat.id):
            sendMsg(message.chat.id, "Do you want to reboot?", InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="ryes"), InlineKeyboardButton("No", callback_data="rno")]]))

    def ping(self, message: Message):
        if AuthCheck(message.chat.id):
            bot.send_message(message.chat.id, "Pong")

    def redocker(self, message: Message):
        if AuthCheck(message.chat.id):
            containerlist: list[str] = getContainers(True)
            if len(containerlist) == 0:
                sendMsg(message.chat.id, "There are no active containers to restart")
                return
            progressMessage: CodeMessage = CodeMessage("PyDocker", "Restarting all containers..")
            progressMessage.create(message.chat.id)
            restartedCount: int = 0
            for container in containerlist:
                containerName: str = getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT)).send()
                if startContainer(container, False, "Unable to restart" + container) == 2:
                        progressMessage.append('🔁')
                        restartedCount += 1
                else:
                        progressMessage.append('❌')
                progressMessage.send()
            sendMsg(message.chat.id, "Restarted {0} of {1} containers".format(restartedCount, len(containerlist)))
    
    def showsvc(self, message: Message):
        if AuthCheck(message.chat.id):
            filteredCDatas: Iterator[Match[str]] = finditer("(?P<ContainerName>[\w-]+) -> (?P<ContainerStatus>\w+)(?: \(\d+\))? (?P<Time>.+)", getContainersData("ALL", "{{.Names}} -> {{.Status}}"))
            wordOffset: int = trunc(config.MSG_LIMIT/3)
            serviceStatus: CodeMessage = CodeMessage("PyDocker", appendRemaining("Container Name", ' ', wordOffset) + appendRemaining("Status", ' ', wordOffset) + appendRemaining("Time", ' ', wordOffset) + '\n')
            serviceStatus.create(message.chat.id)
            for ctData in filteredCDatas:
                for i in range(1,4):
                    serviceStatus.append(appendRemaining(ctData.group(i), ' ', wordOffset))
                serviceStatus.append('\n')
            serviceStatus.send()
                
    def lastbackup(self, message: Message):
        if AuthCheck(message.chat.id):
            if not exists(config.BACKUP_FLAG_PATH):
                sendMsg(message.chat.id, "Unable to get last backup date\nMake sure that a backup has been done before")
                return
            sendMsg(message.chat.id, strftime("The latest backup was done on <i>%b %-d, %Y - %I:%M:%S %p</i>", localtime(getmtime(config.BACKUP_FLAG_PATH))))

    def dockerstart(self, message: Message):
        if AuthCheck(message.chat.id):
            containerlist: list[str] = getContainers()
            progressMessage = CodeMessage("PyDocker", "Starting all containers..")
            progressMessage.create(message.chat.id)
            containerNo: int = len(containerlist)
            startedCount: int = 0
            activeCount: int = 0
            for container in containerlist:
                containerName: str = getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT - 10)).send()
                match startContainer(container, errormsg="Unable to start" + container):
                    case 0:
                        progressMessage.append('🆙')
                        startedCount += 1
                    case 1:
                        progressMessage.append('🟢')
                        activeCount +=  1
                    case -1:
                        progressMessage.append('❌')
                progressMessage.send()

            reply: str = ""
            match [startedCount, activeCount]:
                case [0, containerNo]:
                    reply = "All containers were already active"
                case [containerNo, 0]:
                    reply = "All containers started"
                case _:
                    reply = f"Started {startedCount} of {containerNo} containers ({activeCount} were already active)"
            sendMsg(message.chat.id, reply)

    def dockerstop(self, message: Message):
        if AuthCheck(message.chat.id):
            containerlist: list[str] = getContainers()
            progressMessage = CodeMessage("PyDocker", "Stopping all containers..")
            progressMessage.create(message.chat.id)
            containerNo: int = len(containerlist)
            stoppedCount: int = 0
            inactiveCount: int = 0
            for container in containerlist:
                containerName: str = getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT - 10)).send() # Additional MSG_LIMIT - 1 not required since LF already take 1 charcount of inusable space
                match stopContainer(container, "Unable to stop" + container):
                    case 0:
                        progressMessage.append('⛔')
                        stoppedCount += 1
                    case 1:
                        progressMessage.append('🔴')
                        inactiveCount +=  1
                    case -1:
                        progressMessage.append('❌')
                progressMessage.send()

            reply: str = ""
            match [stoppedCount, inactiveCount]:
                case [0, containerNo]:
                    reply = "All containers were already inactive"
                case [containerNo, 0]:
                    reply = "All containers stopped"
                case _:
                    reply = f"Started {stoppedCount} of {containerNo} containers ({inactiveCount} were already stopped)"
            sendMsg(message.chat.id, reply)

    def uptime(self, message: Message):
        if AuthCheck(message.chat.id):
            commandResult: ProcessOutput = executeCommand("uptime", ["-p"], "Unable to get system uptime")
            if commandResult.good:
                regexFilter: Match[str] = match("up (?:(?P<Days>\d+) days, )?(?:(?P<Hours>\d+) hours, )?(?:(?P<Minutes>\d+) minutes)", commandResult.output)
                days: int = regexFilter.group("Days")
                hours: int = regexFilter.group("Hours")
                minutes: int = regexFilter.group("Minutes")
            sendMsg(message.chat.id, "The server is up by {0}{1}{2} minutes".format(days + " days, " if days is not None else "", hours + " hours and " if hours is not None else "", minutes))

    def dockermenu(self, message: Message):
        if AuthCheck(message.chat.id):
            containerList: list[str] = getContainers()
            createDockerSelectMenu(message.chat.id, containerList, closingRow=[InlineKeyboardButton("Close", callback_data="exit")])

bot.start()
bot.add_commands(Commands())
bot.add_callback(CallbackAction())
while True:
    sleep(1)
