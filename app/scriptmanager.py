from os import listdir, access, X_OK
from os.path import exists, isfile, join, basename
from math import trunc
from script import Script

from config import SCRIPTS_DIRECTORY_PATH
from origamibot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from botutils import sendMsg, editMsg

class ScriptManager:
    def __init__(self, scriptPath: str):
        self.scriptList: list[Script] = []
        self.enabled: bool = False
        self.currentPath = scriptPath
        if not scriptPath or not exists(scriptPath):
            return
        
        for entry in listdir(scriptPath):
              file: str = join(scriptPath, entry)
              if isfile(file) and access(file, X_OK):
                    self.scriptList.append(Script(basename(file), file))
        scriptno: int = len(self.scriptList)
        self.enabled = scriptno > 0
        print(f"{scriptno} script loaded" if self.enabled else "No valid script found")
    
    def find(self, scriptName: str) -> Script | None:
        if self.enabled:
           for script in self.scriptList:
               if script.name == scriptName:
                   return script
        return
    
    def remove(self, script: Script):
        if not script:
            return
        self.scriptList.remove(script)
        self.enabled = len(self.scriptList) > 0
    
    def removeName(self, scriptName: str):
        self.remove(self.find(scriptName))

    def createScriptSelectMenu(self, chatID: int | None = None, callbackSfx: str = "script-", closingRow: list[InlineKeyboardButton] | None = None, messageHolder: Message | None = None) -> Message:
        if not self.enabled:
            if messageHolder:
                editMsg(messageHolder, "No valid script found")
            else:
                sendMsg(chatID, "No valid script found")
            return
        messageMenu: list[list[InlineKeyboardButton]] = []
        scriptNo: int = len(self.scriptList)
        rowOffset: int = trunc(scriptNo/2)

        for i in range(0, rowOffset):
            messageMenu.append([InlineKeyboardButton(self.scriptList[i].name, callback_data=callbackSfx + self.scriptList[i].name), InlineKeyboardButton(self.scriptList[i+rowOffset].name, callback_data=callbackSfx + self.scriptList[i+rowOffset].name)])

        if rowOffset * 2 != scriptNo:
            messageMenu.append([InlineKeyboardButton(self.scriptList[-1].name, callback_data=callbackSfx + self.scriptList[-1].name)])  # -1 obtain the last element of the list

        if closingRow is not None:
            messageMenu.append(closingRow)

        messagetext: str = f"Loaded {scriptNo} script\nSelect which script to launch"
        if messageHolder is None:
            return sendMsg(chatID, messagetext, InlineKeyboardMarkup(messageMenu))
        else:
            return editMsg(messageHolder, messagetext, replyMarkup=InlineKeyboardMarkup(messageMenu))
        
    def listEquals(self, scriptList: list[Script]) -> bool:
        scriptNo: int = len(self.scriptList)
        if scriptNo != len(scriptList):
            return False
        for i in range(0, scriptNo):
            if self.scriptList[i] != scriptList[i]:
                return False
        return True
        
    def reload(self):
        self.__init__(self.currentPath)
        

scriptManager: ScriptManager = ScriptManager(SCRIPTS_DIRECTORY_PATH)