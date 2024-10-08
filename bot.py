from threading import Lock, Timer
from os.path import exists, getmtime, dirname, abspath
from os import _exit as killProcess
from io import StringIO
from time import sleep, strftime, strptime, localtime
from typing import Iterator, Literal
from math import trunc
import requests
from origamibot import OrigamiBot as Bot
from origamibot.util import condition
from subprocess import Popen, PIPE
from origamibot.core.teletypes import *
from re import *
from botutils import DockerChatInstance, docker_manager

try:
    import config
except:
        print("You need to rename \"config.py.template\" to \"config.py\"" if exists(dirname(abspath(__file__)) + "/config.py.template") else "No configuration file found...\nExiting...")
        exit(1)

bot = Bot(config.BOT_TOKEN)
tlock = Lock()

def heartbeat(retries: int = 0):
    if(retries > config.HEARTBEAT_MAX_RETRIES):
        print("[HEARTBEAT] Reached max tries, disabling HEARTBEAT")
        if(config.HEARTBEAT_FAIL_ON_ERROR):
            print("[HEARTBEAT] Detected fail on error, closing now..")
            killProcess(1)
        return

    try:
        requests.head(config.HEARTBEAT_URL)
        if(config.HEARTBEAT_LOG_SUCCESS):
            print("[HEARTBEAT] Ok")
        Timer(config.HEARTBEAT_INTERVAL, heartbeat).start()
    except:
        print("[HEARTBEAT] Unable to reach " + config.HEARTBEAT_URL)
        Timer(config.HEARTBEAT_INTERVAL, heartbeat, [retries + 1]).start()

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

    def bind(self, message: Message):
        self.messageObject = message
        return self

    def create(self, chatID: int, replyMarkup: ReplyMarkup = None):
        self.messageObject = bot.send_message(chatID, "```{0}\n{1}```".format(self.caption, self.message), "MarkdownV2", reply_markup=replyMarkup)

    def send(self, replyMarkup: ReplyMarkup = None):
        self.messageObject = bot.edit_message_text(self.messageObject.chat.id, "```{0}\n{1}```".format(self.caption, self.message), self.messageObject.message_id, parse_mode="MarkdownV2", reply_markup=replyMarkup)

    def clear(self):
        self.message = ""

def AuthCheck(chat_id: int) -> bool:
    allowed = chat_id in config.ALLOWED_CHAT_IDS
    if not allowed:
        bot.send_message(chat_id, "You are not authorized.")
    return allowed

def executeCommand(path: str, args: list[str | int | bool] = [], chatID: int | None = None, errormsg: str | None = None) -> ProcessOutput:
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
        if errormsg and chatID:
            sendMsg(chatID, errormsg)

        print("Executing command: ",end='')
        for part in command:
            print('|' + part + '|', end=' ')
        print()       
        print("Generated this error:" + output.decode("utf-8"))
        return ProcessOutput(exitcode, output.decode("utf-8"))
    return ProcessOutput(exitcode, output.decode("utf-8"))

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

            docker: DockerChatInstance = DockerChatInstance(chatID)
            for i in range(0, rowOffset):
                messageMenu.append([InlineKeyboardButton(docker.getContainerData(CtIDs[i], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i]), InlineKeyboardButton(docker.getContainerData(CtIDs[i+rowOffset], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i+rowOffset])])

            if rowOffset * 2 != containerNo:
                messageMenu.append([InlineKeyboardButton(docker.getContainerData(CtIDs[-1], "{{.Names}}"), callback_data=callbackSfx + CtIDs[-1])]) #-1 obtain the last element of the list

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
    # disk-[N] -> obtain disk device data
    # dport-[ID] -> show currently published port of a docker container

    def logquery(self, cbQuery: CallbackQuery):
        print(f"Recived query: {cbQuery.data} from {cbQuery.from_user.username}")

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dstart-"))
    def dstart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstart-", "")
            bot.answer_callback_query(cbQuery.id, "Container started succesfully" if DockerChatInstance(queryMsg.chat.id).startContainer(CtID) == 0 else "Unable to start this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dstop-"))
    def dstop(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstop-", "")
            bot.answer_callback_query(cbQuery.id, "Container stopped succesfully" if DockerChatInstance(queryMsg.chat.id).stopContainer(CtID) == 0 else "Unable to stop this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("drestart-"))
    def drestart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("drestart-", "")
            bot.answer_callback_query(cbQuery.id, "Container restarted succesfully" if DockerChatInstance(queryMsg.chat.id).startContainer(CtID, False) == 2 else "Unable to restart this container")
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
            virtualFile.name = f'{DockerChatInstance(chatID).getContainerData(CtID, "{{.Names}}")} ({strftime("%b %-d %Y %H-%M-%S", localtime())}).log'
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
            docker: DockerChatInstance = DockerChatInstance(menuMessage.chat.id)
            CtID: str = cbQuery.data.replace("docker-", "")
            if CtID in docker.getContainers():
                ctData: str = match("(?P<ContainerName>[\w-]+) -> (?P<ContainerStatus>\w+)(?: \(\d+\))? (?P<Time>.+)\[\d+.?\w+ \(virtual (?P<Size>.+)\)\]\/(?P<UpdTime>.+)", docker.getContainerData(CtID, "{{.Names}} -> {{.Status}}[{{.Size}}]/{{.CreatedAt}}"))
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
                    buttons.append([InlineKeyboardButton("Ports", callback_data=f"dport-{CtID}")])
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
            createDockerSelectMenu(None, DockerChatInstance(menuMessage.chat.id).getContainers(), closingRow=[InlineKeyboardButton("Close", callback_data="exit")], messageHolder=menuMessage)
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

    @condition(lambda c, cbQuery: cbQuery.data.startswith("disk-"))
    def diskInfo(self, cbQuery: CallbackQuery):
        message: Message = cbQuery.message
        if AuthCheck(message.chat.id):
            diskNumber: int = int(cbQuery.data.replace("disk-", ""))
            command: ProcessOutput = executeCommand("df",["--type", "btrfs", "--type", "ext4", "--type", "ext3", "--type", "ext2", "--type", "vfat", "--type", "iso9660", "--type", "ntfs", "-TH"])
            if not command.good:
                if cbQuery.id:
                    bot.answer_callback_query(cbQuery.id, "Unable to get disk data")
                else:
                    sendMsg(message.chat.id, "Unable to get disk data")
                return
            diskArray: list[tuple] = findall(r'\/dev\/(?P<DiskName>\w+) +(?P<Type>\w+) +(?P<TotSpace>\d+,?\.?\d+\w+?) +(?P<UsedSpace>\d+,?\.?\d+\w+?) +(?P<RemSpace>(?:\d+,?\.?\d+\w+? | 0)) +\d+% +(?P<Mount>.+)', command.output)
            maxDiskNumber: int = len(diskArray) - 1
            buttons = []
            if diskNumber == 0:
                buttons.append([InlineKeyboardButton("→",callback_data=f'disk-{diskNumber+1}')])
            if 0 < diskNumber < maxDiskNumber:
                buttons.append([InlineKeyboardButton("←",callback_data=f'disk-{diskNumber-1}'), InlineKeyboardButton("→",callback_data=f'disk-{diskNumber+1}')])
            if diskNumber == maxDiskNumber:
                buttons.append([InlineKeyboardButton("←",callback_data=f'disk-{diskNumber-1}')])
            buttons.append([InlineKeyboardButton("Close",callback_data="exit")])
            editMsg(message,f'<b><em>Disk {diskNumber}</em></b>\n├─ Name: <b>{diskArray[diskNumber][0]}</b>\n├─ File System: {diskArray[diskNumber][1]}\n├─ Mount: <code>{diskArray[diskNumber][5]}</code> \n├─ Total Space: {diskArray[diskNumber][2]}\n├─ Used Space: {diskArray[diskNumber][3]}\n└─ Remaining Space: {diskArray[diskNumber][4]}', replyMarkup=InlineKeyboardMarkup(buttons))
            if cbQuery.id:
                bot.answer_callback_query(cbQuery.id)

    @condition(lambda c, cbQuery: cbQuery.data.startswith("dport-"))
    def dport(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dport-", "")
            portCmd = executeCommand("docker", ["container", "port", CtID])
            if not portCmd.good:
                bot.answer_callback_query(cbQuery.id, "Unable to get this container ports")
                return
            elif(not portCmd.output or portCmd.output.isspace()):
                bot.answer_callback_query(cbQuery.id, "There are no active published ports")
                return
            wordOffset = trunc(config.MSG_LIMIT/3)
            portMsg: CodeMessage = CodeMessage("PyDocker", appendRemaining("Container Port", ' ', wordOffset) + appendRemaining("Protocol", ' ', wordOffset) + appendRemaining("Host Port", ' ', wordOffset))
            portMsg.bind(queryMsg)
            for ctData in finditer("(?P<CtPort>\d+)\/(?P<Proto>\w+) -> (?:(?:[\d.]+)|(?:\[(?P<SckIP>[a-f\d:]+)\])):(?P<SckPort>\d+)", portCmd.output):
                portMsg.append('\n' + appendRemaining(ctData.group("CtPort"), ' ', wordOffset) + appendRemaining("  " + ctData.group("Proto").upper(), ' ', wordOffset) + appendRemaining(ctData.group("SckPort"), ' ', wordOffset))
            portMsg.send(InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=f"docker-{CtID}")]]))
            bot.answer_callback_query(cbQuery.id)

class Commands:

    def backup(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.BACKUP_SCRIPT_PATH, config.BACKUP_SCRIPT_ARGS, message.chat.id, "Error during system backup")
                    
    def updatedb(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.NGINX_DB_UPDATE_PATH, chatID=message.chat.id, errormsg= "Error while updating nginx IP database")

    def reboot(self, message: Message):
        if AuthCheck(message.chat.id):
            sendMsg(message.chat.id, "Do you want to reboot?", InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="ryes"), InlineKeyboardButton("No", callback_data="rno")]]))

    def ping(self, message: Message):
        if AuthCheck(message.chat.id):
            bot.send_message(message.chat.id, "Pong")

    def redocker(self, message: Message):
        if AuthCheck(message.chat.id):
            docker: DockerChatInstance = DockerChatInstance(message.chat.id)
            containerlist: list[str] = docker.getContainers(True)
            if len(containerlist) == 0:
                sendMsg(message.chat.id, "There are no active containers to restart")
                return
            progressMessage: CodeMessage = CodeMessage("PyDocker", "Restarting all containers..")
            progressMessage.create(message.chat.id)
            restartedCount: int = 0
            for container in containerlist:
                containerName: str = docker.getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT)).send()
                if docker.startContainer(container, False, "Unable to restart" + container) == 2:
                        progressMessage.append('🔁')
                        restartedCount += 1
                else:
                        progressMessage.append('❌')
                progressMessage.send()
            sendMsg(message.chat.id, "Restarted {0} of {1} containers".format(restartedCount, len(containerlist)))
    
    def showsvc(self, message: Message):
        if AuthCheck(message.chat.id):
            filteredCDatas: Iterator[Match[str]] = finditer("(?P<ContainerName>[\w-]+) -> (?P<ContainerStatus>\w+)(?: \(\d+\))? (?P<Time>.+)", DockerChatInstance(message.chat.id).getContainersData("ALL", "{{.Names}} -> {{.Status}}"))
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
            docker: DockerChatInstance = DockerChatInstance(message.chat.id)
            containerlist: list[str] = docker.getContainers()
            progressMessage = CodeMessage("PyDocker", "Starting all containers..")
            progressMessage.create(message.chat.id)
            containerNo: int = len(containerlist)
            startedCount: int = 0
            activeCount: int = 0
            for container in containerlist:
                containerName: str = docker.getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT - 10)).send()
                match docker.startContainer(container, errormsg="Unable to start" + container):
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
            docker: DockerChatInstance = DockerChatInstance(message.chat.id)
            containerlist: list[str] = docker.getContainers()
            progressMessage = CodeMessage("PyDocker", "Stopping all containers..")
            progressMessage.create(message.chat.id)
            containerNo: int = len(containerlist)
            stoppedCount: int = 0
            inactiveCount: int = 0
            for container in containerlist:
                containerName: str = docker.getContainerData(container, "{{.Names}}")
                progressMessage.append(appendRemaining('\n' + containerName, ' ', config.MSG_LIMIT - 10)).send() # Additional MSG_LIMIT - 1 not required since LF already take 1 charcount of inusable space
                match docker.stopContainer(container, "Unable to stop" + container):
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
            commandResult: ProcessOutput = executeCommand("uptime", ["-p"], message.chat.id, "Unable to get system uptime")
            if commandResult.good:
                regexFilter: Match[str] = match("up (?:(?P<Weeks>\d+) weeks?, )?(?:(?P<Days>\d+) days?, )?(?:(?P<Hours>\d+) hours?, )?(?:(?P<Minutes>\d+) minutes?)", commandResult.output)
                weeks: int = regexFilter.group("Weeks")
                days: int = regexFilter.group("Days")
                hours: int = regexFilter.group("Hours")
                minutes: int = regexFilter.group("Minutes")
            sendMsg(message.chat.id, "The server is up by {0}{1}{2}{3} minutes".format(weeks + " weeks, " if weeks is not None else "", days + " days, " if days is not None else "", hours + " hours and " if hours is not None else "", minutes))

    def dockermenu(self, message: Message):
        if AuthCheck(message.chat.id):
            containerList: list[str] = DockerChatInstance(message.chat.id).getContainers()
            createDockerSelectMenu(message.chat.id, containerList, closingRow=[InlineKeyboardButton("Close", callback_data="exit")])

    def cleanup(self, message: Message):
        if (AuthCheck(message.chat.id)):
            commandResult: ProcessOutput = executeCommand("docker", ["image", "prune", "-a", "-f"], message.chat.id, "Unable to clean docker images")
            if(commandResult.good):
                filteredOutput: Match[str] = search("(?<=space: )(?P<Size>[\d.]+)(?P<Unit>\w+)", commandResult.output)
                freedDSpace: float = round(float(filteredOutput.group("Size")), 2)
                if(freedDSpace == 0):
                    sendMsg(message.chat.id, "No dangling images found")
                    return
                sendMsg(message.chat.id, f"Cleaned up <b>{freedDSpace}{filteredOutput.group('Unit')}</b>")

    def diskinfo(self, message: Message):
        if AuthCheck(message.chat.id):
            reply: Message = sendMsg(message.chat.id, "Obtaining data...")
            CallbackAction.diskInfo(None, CallbackQuery(None, reply.from_user, str(reply.chat), reply, data="disk-0"))

    def showusr(self,message: Message):
        if AuthCheck(message.chat.id):
            command = executeCommand("w",["-h","-i"], message.chat.id, "Unable to get connected users")
            if not command.good:
                return
            connectedUsers: list[tuple] = findall(r'(\w+)\s+pts\/\d+\s+((?:(?:[\d.]*){4})|(?:\[?(?:[a-f0-9:]+)\]?))\s+(\d+:\d+).+',command.output)
            if len(connectedUsers) == 0:
                sendMsg(message.chat.id, "There are currently no users connected to the server")
                return
            wordOffset: int = trunc(config.MSG_LIMIT/3)
            userMessage: CodeMessage = CodeMessage("PyBot",appendRemaining("User", ' ', wordOffset) + appendRemaining("IP Address", ' ', wordOffset) + appendRemaining("Login Time", ' ', wordOffset))
            userMessage.create(message.chat.id)
            for user in connectedUsers:
                userMessage.append('\n')
                for group in range(0,3):
                    userMessage.append(appendRemaining(user[group], ' ', wordOffset))
            userMessage.send()

if(config.HEARTBEAT_ENABLED):
    Timer(5, heartbeat).start()

#TODO: Refactor and remove this abomination
docker_manager.executeCommand = executeCommand
docker_manager.ProcessOutput = ProcessOutput

bot.start()
bot.add_commands(Commands())
bot.add_callback(CallbackAction())
while True:
    sleep(1)
