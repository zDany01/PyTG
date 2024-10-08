from math import trunc
from os.path import exists, getmtime
from re import *
from time import strftime, localtime
from typing import Iterator
from origamibot.types import *

import config
from shared import botInstance as bot
from botutils import ProcessOutput, AuthCheck, sendMsg, executeCommand, appendRemaining, editMsg
from code_message import CodeMessage
from docker_manager import DockerManager as DockerChatInstance, createDockerSelectMenu
from callback_actions import CallbackActions

class Commands:
    def backup(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.BACKUP_SCRIPT_PATH, config.BACKUP_SCRIPT_ARGS, message.chat.id, "Error during system backup")

    def updatedb(self, message: Message):
        if AuthCheck(message.chat.id):
            executeCommand(config.NGINX_DB_UPDATE_PATH, chatID=message.chat.id, errormsg="Error while updating nginx IP database")

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
            for ctData in filteredCDatas:
                for i in range(1, 4):
                    serviceStatus.append(appendRemaining(ctData.group(i), ' ', wordOffset))
                serviceStatus.append('\n')
            serviceStatus.create(message.chat.id)

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
                        activeCount += 1
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
                        inactiveCount += 1
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
            if commandResult.good:
                filteredOutput: Match[str] = search("(?<=space: )(?P<Size>[\d.]+)(?P<Unit>\w+)", commandResult.output)
                freedDSpace: float = round(float(filteredOutput.group("Size")), 2)
                if freedDSpace == 0:
                    sendMsg(message.chat.id, "No dangling images found")
                    return
                sendMsg(message.chat.id, f"Cleaned up <b>{freedDSpace}{filteredOutput.group('Unit')}</b>")

    def diskinfo(self, message: Message):
        if AuthCheck(message.chat.id):
            reply: Message = sendMsg(message.chat.id, "Obtaining data...")
            CallbackActions.diskInfo(None, CallbackQuery(None, reply.from_user, str(reply.chat), reply, data="disk-0"))

    def showusr(self, message: Message):
        if AuthCheck(message.chat.id):
            command: ProcessOutput = executeCommand("w", ["-h", "-i"], message.chat.id, "Unable to get connected users")
            if not command.good:
                return
            connectedUsers: list[tuple] = findall(r'(\w+)\s+pts\/\d+\s+((?:(?:[\d.]*){4})|(?:\[?(?:[a-f0-9:]+)\]?))\s+(\d+:\d+).+', command.output)
            if len(connectedUsers) == 0:
                sendMsg(message.chat.id, "There are currently no users connected to the server")
                return
            wordOffset: int = trunc(config.MSG_LIMIT/3)
            userMessage: CodeMessage = CodeMessage("PyBot", appendRemaining("User", ' ', wordOffset) + appendRemaining("IP Address", ' ', wordOffset) + appendRemaining("Login Time", ' ', wordOffset))

            for user in connectedUsers:
                userMessage.append('\n')
                for group in range(0, 3):
                    userMessage.append(appendRemaining(user[group], ' ', wordOffset))
            userMessage.create(message.chat.id)