# PyTG
A Python telegram bot to manage a server remotely

## Requirements
This application requires some installed software before being used
- Python
  - python3
  - python3-pip
  - python3-virtualenv
  - python3-wheel (optional)
- Docker

## Installation
You need to execute the `install` file to install this bot as a system service.
```bash
sudo ./install
```
This will create a virtual environment in your folder where the script will automatically install all the dependencies.

If you want to uninstall the service you need to execute the `uninstall` script
```bash
sudo ./uninstall
```

If you just want to execute the software without installing it as a service you can create a virtual environment called TGBot and then install the requirements.txt file
```bash
virtualenv TGBot 
source ./TGBot/bin/activate
pip3 install -r requirements.txt
```
From here you can either start manually the python script by accessing first to the virtual environment every time or you can deactivate it and just use the `pystart` file
> Remember to run the Python bot with privileges

## Bot settings
Before using the app you need to rename the `config.py.template` file (which is located in the app subdirectory) to `config.py` and modify some settings in it:

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `BOT_TOKEN` | `string` | **Required**. Telegram bot token (get one from [@BotFather](https://t.me/BotFather)) |
| `ALLOWED_CHAT_IDS` | `list[int]` | **Required**. List of ChatIDs that are allowed to use this bot|
| `MSG_LIMIT` | `int` | **Required**. Row character limit, if unsure use 60 |
| `BACKUP_SCRIPT_PATH` | `string` |  Path to your bash backup script |
| `BACKUP_SCRIPT_ARGS` | `list[string]` |  Arguments for your backup script|
| `BACKUP_FLAG_PATH` | `string` | Path for backup updated file |
| `NGINX_DB_UPDATE_PATH` | `string` | Path to your nginx database update bash script |
| `HEARTBEAT_ENABLED` | `bool` | Enable or Disable the heartbeat service |
| `HEARTBEAT_URL` | `string` | API URL to fetch |
| `HEARTBEAT_INTERVAL` | `int` | Time to wait (in seconds) before fetching again |
| `HEARTBEAT_MAX_RETRIES` | `int` | The maximum number of attempts before disabling the heartbeat service |
| `HEARTBEAT_FAIL_ON_ERROR` | `bool` | Closes the program if the heartbeat service is not reachable |
| `HEARTBEAT_LOG_SUCCESS` | `bool` | Logs the successful requests |

## Usage
### Manual
To start the bot manually use the `pystart` file
```bash
sudo ./pystart
```
### Service
Service status
```bash
sudo systemctl status PyTG
```
Start the service
```bash
sudo systemctl start PyTG
```
Stop the service
```bash
sudo systemctl stop PyTG
```
Disable the service (stop and prevent it from running automatically)
```bash
sudo systemctl disable PyTG
sudo systemctl stop PyTG
```
Enable the service
```bash
sudo systemctl enable PyTG
sudo systemctl start PyTG
```

# Contributing
See `CONTRIBUTING.md` for more information

## License
Distributed under the MIT License. See `LICENSE` for more information.
