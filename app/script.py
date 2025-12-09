from botutils import ProcessOutput, executeCommand
class Script:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
    
    def execute(self) -> ProcessOutput:
        print(f"Running script {self.name}")
        return executeCommand(self.path)