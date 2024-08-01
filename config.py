# Bot Settings
#Insert here your telegram bot token
BOT_TOKEN = ""
#Authorized ChatID that can use this bot (Replace 0 with your chatID)
CHAT_ID = 0
#CodeMessage row character limit, if unsure use 60
MSG_LIMIT = 60

# Script settings
BACKUP_SCRIPT_PATH = ""
BACKUP_SCRIPT_ARGS = [] #Ex [arg1, arg2, arg3]
#This is the file that get updated when a backup script is executed
# Default: <BackupScriptWorkingDirectory>/update
# Change manually if different
BACKUP_FLAG_PATH = BACKUP_SCRIPT_PATH[0:BACKUP_SCRIPT_PATH.rfind("/")] + "/update"
NGINX_DB_UPDATE_PATH = ""
