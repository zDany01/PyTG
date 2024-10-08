from math import trunc
from time import strftime, strptime, localtime
from io import StringIO
from re import *
from origamibot.util import condition
from origamibot.types import *

import config
from shared import botInstance as bot
from botutils import ProcessOutput, AuthCheck, sendMsg, executeCommand, appendRemaining, editMsg
from docker_manager import DockerManager as DockerChatInstance, createDockerSelectMenu
from code_message import CodeMessage
class CallbackActions:
    # CallBack -> Action
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

    @condition(lambda _, cbQuery: cbQuery.data.startswith("dstart-"))
    def dstart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstart-", "")
            bot.answer_callback_query(cbQuery.id, "Container started succesfully" if DockerChatInstance(queryMsg.chat.id).startContainer(CtID) == 0 else "Unable to start this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda _, cbQuery: cbQuery.data.startswith("dstop-"))
    def dstop(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dstop-", "")
            bot.answer_callback_query(cbQuery.id, "Container stopped succesfully" if DockerChatInstance(queryMsg.chat.id).stopContainer(CtID) == 0 else "Unable to stop this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda _, cbQuery: cbQuery.data.startswith("drestart-"))
    def drestart(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("drestart-", "")
            bot.answer_callback_query(cbQuery.id, "Container restarted succesfully" if DockerChatInstance(queryMsg.chat.id).startContainer(CtID, False) == 2 else "Unable to restart this container")
            self.createMenu(CallbackQuery(cbQuery.id, bot.get_me(), cbQuery.chat_instance, queryMsg, cbQuery.inline_message_id, "docker-" + CtID), True)

    @condition(lambda _, cbQuery: cbQuery.data.startswith("dlog-"))
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

    @condition(lambda _, cbQuery: cbQuery.data == "exit")
    def closeMenu(self, cbQuery: CallbackQuery):
        menuMessage: Message = cbQuery.message
        if AuthCheck(menuMessage.chat.id):
            editMsg(menuMessage, "Menu closed")
            bot.answer_callback_query(cbQuery.id)

    @condition(lambda _, cbQuery, updateOnly=False: cbQuery.data.startswith("docker-") or updateOnly)
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
                ctLastUpd: str = strftime("<i>%b %-d, %Y - %I:%M %p</i>", strptime(ctData.group("UpdTime"), "%Y-%m-%d %H:%M:%S %z %Z"))

                buttons = []
                if ctRunning:
                    buttons.append([InlineKeyboardButton("Stop", callback_data=f"dstop-{CtID}"), InlineKeyboardButton("Restart", callback_data=f"drestart-{CtID}")])
                    buttons.append([InlineKeyboardButton("Ports", callback_data=f"dport-{CtID}"), InlineKeyboardButton("Logs", callback_data=f"dlog-{CtID}")])
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

    @condition(lambda _, cbQuery: cbQuery.data == "reopen")
    def reOpenMenu(self, cbQuery: CallbackQuery):
        menuMessage: Message = cbQuery.message
        if AuthCheck(menuMessage.chat.id):
            createDockerSelectMenu(None, DockerChatInstance(menuMessage.chat.id).getContainers(), closingRow=[InlineKeyboardButton("Close", callback_data="exit")], messageHolder=menuMessage)
            bot.answer_callback_query(cbQuery.id)

    @condition(lambda _, cbQuery: cbQuery.data == "ryes")
    def ryes(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            bot.answer_callback_query(cbQuery.id, "Rebooting...")
            editMsg(queryMsg, "System Rebooted")
            executeCommand("reboot")

    @condition(lambda _, cbQuery: cbQuery.data == "rno")
    def rno(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            editMsg(queryMsg, "Operation aborted.")
            bot.answer_callback_query(cbQuery.id)

    @condition(lambda _, cbQuery: cbQuery.data.startswith("disk-"))
    def diskInfo(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            diskNumber: int = int(cbQuery.data.replace("disk-", ""))
            command: ProcessOutput = executeCommand("df", ["--type", "btrfs", "--type", "ext4", "--type", "ext3", "--type", "ext2", "--type", "vfat", "--type", "iso9660", "--type", "ntfs", "-TH"])
            if not command.good:
                if cbQuery.id:
                    bot.answer_callback_query(cbQuery.id, "Unable to get disk data")
                else:
                    sendMsg(queryMsg.chat.id, "Unable to get disk data")
                return
            diskArray: list[tuple] = findall(r'\/dev\/(?P<DiskName>\w+) +(?P<Type>\w+) +(?P<TotSpace>\d+,?\.?\d+\w+?) +(?P<UsedSpace>\d+,?\.?\d+\w+?) +(?P<RemSpace>(?:\d+,?\.?\d+\w+? | 0)) +\d+% +(?P<Mount>.+)', command.output)
            maxDiskNumber: int = len(diskArray) - 1
            buttons = []
            if diskNumber == 0:
                buttons.append([InlineKeyboardButton("→", callback_data=f'disk-{diskNumber+1}')])
            if 0 < diskNumber < maxDiskNumber:
                buttons.append([InlineKeyboardButton("←", callback_data=f'disk-{diskNumber-1}'), InlineKeyboardButton("→", callback_data=f'disk-{diskNumber+1}')])
            if diskNumber == maxDiskNumber:
                buttons.append([InlineKeyboardButton("←", callback_data=f'disk-{diskNumber-1}')])
            buttons.append([InlineKeyboardButton("Close", callback_data="exit")])
            editMsg(queryMsg, f'<b><em>Disk {diskNumber}</em></b>\n├─ Name: <b>{diskArray[diskNumber][0]}</b>\n├─ File System: {diskArray[diskNumber][1]}\n├─ Mount: <code>{diskArray[diskNumber][5]}</code> \n├─ Total Space: {diskArray[diskNumber][2]}\n├─ Used Space: {diskArray[diskNumber][3]}\n└─ Remaining Space: {diskArray[diskNumber][4]}', replyMarkup=InlineKeyboardMarkup(buttons))
            if cbQuery.id:
                bot.answer_callback_query(cbQuery.id)

    @condition(lambda _, cbQuery: cbQuery.data.startswith("dport-"))
    def dport(self, cbQuery: CallbackQuery):
        queryMsg: Message = cbQuery.message
        if AuthCheck(queryMsg.chat.id):
            CtID: str = cbQuery.data.replace("dport-", "")
            portCmd: ProcessOutput = executeCommand("docker", ["container", "port", CtID])
            if not portCmd.good:
                bot.answer_callback_query(cbQuery.id, "Unable to get this container ports")
                return
            elif not portCmd.output or portCmd.output.isspace():
                bot.answer_callback_query(cbQuery.id, "There are no active published ports")
                return
            wordOffset = trunc(config.MSG_LIMIT/3)
            portMsg: CodeMessage = CodeMessage("PyDocker", appendRemaining("Container Port", ' ', wordOffset) + appendRemaining("Protocol", ' ', wordOffset) + appendRemaining("Host Port", ' ', wordOffset))
            portMsg.bind(queryMsg)
            for ctData in finditer("(?P<CtPort>\d+)\/(?P<Proto>\w+) -> (?:(?:[\d.]+)|(?:\[(?P<SckIP>[a-f\d:]+)\])):(?P<SckPort>\d+)", portCmd.output):
                portMsg.append('\n' + appendRemaining(ctData.group("CtPort"), ' ', wordOffset) + appendRemaining("  " + ctData.group("Proto").upper(), ' ', wordOffset) + appendRemaining(ctData.group("SckPort"), ' ', wordOffset))
            portMsg.send(InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=f"docker-{CtID}")]]))
            bot.answer_callback_query(cbQuery.id)
