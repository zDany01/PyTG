from origamibot.types import Message, ReplyMarkup
from shared import botInstance as bot

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