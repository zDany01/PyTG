# PyTG

**PyTG** is a Python-based Telegram bot designed to manage a server remotely. It allows administrators to execute system maintenance tasks, manage backups, and monitor server status directly via Telegram.

## 📋 Prerequisites

Ensure the following software is installed on your system before proceeding:

* **Docker** (Required for container management)
* **Python 3**
    * `python3-pip`
    * `python3-virtualenv`

## 🛠️ Installation

You can install PyTG as a background service or set it up manually for standalone execution.

### Option A: Service Installation (Recommended)
This method automates the virtual environment creation and registers the Systemd service.

1.  **Prepare the scripts**
    ```bash
    chmod +x install uninstall pystart
    ```

2.  **Run the Installer**
    Execute the install script with root privileges.
    ```bash
    sudo ./install
    ```

### Option B: Manual Setup (No Service)
If you just want to execute the software without installing it as a service, you can create a virtual environment (e.g., named `TGBot`) and install the dependencies manually.

```bash
virtualenv TGBot 
source ./TGBot/bin/activate
pip3 install -r requirements.txt
```

From here, you can start the python script manually by accessing the virtual environment every time, or you can deactivate it and simply use the `pystart` wrapper.

> **Note:** If using `pystart` with this method, ensure the `APP_NAME` variable inside the `pystart` file matches your virtual environment folder name (e.g., `TGBot`).

## ⚙️ Configuration

Before the bot can function, you must configure your secrets and settings.

1.  **Create the Config File**<br>
    Rename the template file in the app subdirectory:
    ```bash
    mv app/config.py.template app/config.py
    ```

2.  **Edit Settings**<br>
    Open `app/config.py` and configure the following parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `BOT_TOKEN` | `string` | **Required**. Your Telegram bot token (via [@BotFather](https://t.me/BotFather)) |
| `ALLOWED_CHAT_IDS` | `list[int]` | **Required**. List of ChatIDs allowed to interact with the bot |
| `MSG_LIMIT` | `int` | **Required**. Character limit per row (Default: `60`) |
| `BACKUP_SCRIPT_PATH` | `string` | Absolute path to your bash backup script |
| `BACKUP_SCRIPT_ARGS` | `list[string]` | Arguments to pass to the backup script |
| `BACKUP_FLAG_PATH` | `string` | Path for the backup status flag file |
| `NGINX_DB_UPDATE_PATH` | `string` | Path to your Nginx database update script |
| `HEARTBEAT_ENABLED` | `bool` | Enable/Disable the heartbeat monitoring service |
| `HEARTBEAT_URL` | `string` | The API URL to fetch for heartbeat checks |
| `HEARTBEAT_INTERVAL` | `int` | Interval (in seconds) between heartbeat checks |
| `HEARTBEAT_MAX_RETRIES` | `int` | Max attempts before disabling heartbeat on failure |
| `HEARTBEAT_FAIL_ON_ERROR`| `bool` | If `True`, the program closes if the heartbeat fails |
| `HEARTBEAT_LOG_SUCCESS` | `bool` | If `True`, logs every successful heartbeat request |

## 🚀 Usage

### Service Management
If installed via **Option A**, PyTG runs as a background service.

* **Start Service:** `sudo systemctl start PyTG`
* **Stop Service:** `sudo systemctl stop PyTG`
* **Check Status:** `sudo systemctl status PyTG`
* **Enable on Boot:** `sudo systemctl enable PyTG`
* **Disable Boot Start:** `sudo systemctl disable PyTG`

### Manual Execution
If you set up the project using **Option B** (or want to debug the service installation), you can use the wrapper script to handle the environment activation automatically:

```bash
sudo ./pystart
```

> **Note:** The bot requires root privileges to execute system maintenance tasks.

## 🗑️ Uninstallation

If you installed the service use the uninstaller to remove the service, delete the virtual environment, and clean up the systemd unit files:

```bash
sudo ./uninstall
```

## 🤝 Contributing
See `CONTRIBUTING.md` for guidelines on how to contribute to this project.

## 🌟 Credits
* [origamibot](https://github.com/cmd410/OrigamiBot) - The Python library used for Telegram bot interactions.

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
