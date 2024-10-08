from typing import Literal

executeCommand = None
ProcessOutput = None

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