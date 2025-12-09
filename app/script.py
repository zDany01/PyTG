from botutils import ProcessOutput, executeCommand
class Script:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.path == other.path
        return False
    
    def execute(self) -> ProcessOutput:
        print(f"Running script {self.name}")
        return executeCommand(self.path)