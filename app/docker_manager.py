from math import trunc
from typing import Literal
from origamibot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from botutils import ProcessOutput, executeCommand, sendMsg, editMsg

class DockerManager:
    def __init__(self, chatID: int):
        self.chatID = chatID

    def getContainers(self, activeOnly: bool = False) -> list[str]:
        containerlistprc: ProcessOutput = executeCommand("docker", ["ps", "-a", "-q"] if not activeOnly else ["ps", "-q"], self.chatID, "Unable to get container list")
        return containerlistprc.output.splitlines() if containerlistprc.good else None

    def getContainersData(self, Containers: Literal["ALL", "ACTIVE"] = "ACTIVE", formatString: str = "") -> str: #merge
        return executeCommand("docker", ["ps", "-a", "--format", formatString] if Containers == "ALL" else ["ps", "--format", formatString]).output

    def getContainerData(self, CtID: str, formatString: str = None) -> str: #merge
        return executeCommand("docker", ["ps", "-a", "--filter", "id=" + CtID, "--format", formatString] if formatString is not None else ["ps", "-a", "--filter", "id=" + CtID], self.chatID, "Unable to get container data for CtID: " + CtID).output.strip()

    def getContainerDataList(self, CtIDs: list[str], formatString: str = None) -> list[str]:
        dataList: list[str] = []
        for CtID in CtIDs:
            dataList.append(self.getContainerData(CtID, formatString))
        return dataList

    def startContainer(self, CtID: str, startOnly: bool = True, errormsg: str = "") -> int: #merge
        """
        :param errormsg: this message will be displayed if there is an error when executing the start/restart command NOT if the container is already started
        :return 0: if started correctly
        :return 1: if already started
        :return 2: if restarted correctly
        :return -1: if an error occured during starting/restarting
        """
        if self.getContainerData(CtID, "{{.Status}}").startswith("Up"):
            if (startOnly):
                return 1
            return 2 if executeCommand("docker", ["restart", CtID], self.chatID, errormsg).good else -1
        return 0 if executeCommand("docker", ["start", CtID], self.chatID, errormsg).good else -1

    def startContainers(self, CtIDs: list[str], startOnly: bool = True) -> list[int]:
        startResult: list[int] = []
        for CtID in CtIDs:
            startResult.append(self.startContainer(CtID, startOnly))
        return startResult

    def stopContainer(self, CtID: str, errormsg: str = "") -> int: #merge
        """
        :param errormsg: this message will be displayed if there is an error when executing the stop command NOT if the container is already stopped
        :return 0: if stopped correctly
        :return 1: if already stopped
        :return -1: if an error occured during stopping
        """
        if self.getContainerData(CtID, "{{.Status}}").startswith("Exited"):
            return 1
        return 0 if executeCommand("docker", ["stop", CtID], self.chatID, errormsg).good else -1

    def stopContainers(self, CtIDs: list[str]) -> list[int]:
        stopResults: list[int] = []
        for CtID in CtIDs:
            stopResults.append(self.stopContainer(CtID))
        return stopResults


def createDockerSelectMenu(chatID: int | None, CtIDs: list[str], callbackSfx: str = "docker-", closingRow: list[InlineKeyboardButton] | None = None, messageHolder: Message | None = None) -> Message:
    messageMenu: list[list[InlineKeyboardButton]] = []
    containerNo: int = len(CtIDs)
    rowOffset: int = trunc(containerNo/2)

    docker: DockerManager = DockerManager(chatID)
    for i in range(0, rowOffset):
        messageMenu.append([InlineKeyboardButton(docker.getContainerData(CtIDs[i], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i]), InlineKeyboardButton(docker.getContainerData(CtIDs[i+rowOffset], "{{.Names}}"), callback_data=callbackSfx + CtIDs[i+rowOffset])])

    if rowOffset * 2 != containerNo:
        messageMenu.append([InlineKeyboardButton(docker.getContainerData(CtIDs[-1], "{{.Names}}"), callback_data=callbackSfx + CtIDs[-1])])  # -1 obtain the last element of the list

    if closingRow is not None:
        messageMenu.append(closingRow)

    if messageHolder is None:
        return sendMsg(chatID, "Select a docker container", InlineKeyboardMarkup(messageMenu))
    else:
        return editMsg(messageHolder, "Select a docker container", replyMarkup=InlineKeyboardMarkup(messageMenu))