from subprocess import Popen, PIPE
from origamibot.types import Message, ReplyMarkup
import config
from shared import botInstance as bot, threadLock

class ProcessOutput:
    def __init__(self, exitcode: int, output: str):
        self.ecode = exitcode
        self.output = output
        self.good = exitcode == 0


def AuthCheck(chat_id: int) -> bool:
    allowed: bool = chat_id in config.ALLOWED_CHAT_IDS
    if not allowed:
        bot.send_message(chat_id, "You are not authorized.")
    return allowed

def sendMsg(chatID: int, message: str, replyMarkup: ReplyMarkup = None) -> Message:
    return bot.send_message(chatID, "<b>PyBot</b>\n" + message, "HTML", reply_markup=replyMarkup)

def executeCommand(path: str, args: list[str | int | bool] = [], chatID: int | None = None, errormsg: str | None = None) -> ProcessOutput:
    threadLock.acquire()
    command: list[str] = [path]
    command.extend(args)
    print(f"Executing {path} with args: " + "".join(map(str, args)))

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
        threadLock.release()

    if exitcode != 0:
        if errormsg and chatID:
            sendMsg(chatID, errormsg)

        print("Executing command: ", end='')
        for part in command:
            print('|' + part + '|', end=' ')
        print()
        print("Generated this error:" + output.decode("utf-8"))
    return ProcessOutput(exitcode, output.decode("utf-8"))

def appendRemaining(str: str, c: str, maxLength: int) -> str:
    for _ in range(maxLength-len(str)):
        str += c
    return str

def editMsg(message: Message, content: str, append: bool = False, parsemode: str = "HTML", replyMarkup: ReplyMarkup | None = None) -> Message:
    return bot.edit_message_text(message.chat.id, message.text + content if append else "<b>PyBot</b>\n" + content, message.message_id, parse_mode=parsemode, reply_markup=replyMarkup)