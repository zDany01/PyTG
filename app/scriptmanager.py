from os import listdir, access, X_OK
from os.path import exists, isfile, join, basename
from script import Script

class ScriptManager:
    def __init__(self, scriptPath: str):
        self.scriptList: list[Script]
        self.enabled: bool = False
        if not scriptPath or not exists(scriptPath):
            return
        
        for entry in listdir(scriptPath):
              file: str = join(scriptPath, entry)
              if isfile(file) and access(file, X_OK):
                    self.scriptList.append(Script(basename(file), file))
        scriptno: int = len(scriptPath)
        self.enabled = scriptno > 0
        print(f"{scriptno} script loaded" if self.enabled else "No valid script found")
    
    def find(self, scriptName: str) -> Script | None:
        if self.enabled:
           for script in self.scriptList:
               if script.name == scriptName:
                   return script
        return