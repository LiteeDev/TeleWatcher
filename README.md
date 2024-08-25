# Telegram Chat Management Bot

A Telegram bot designed for chat management, including keyword monitoring, user muting, message deletion, and clearing chat messages. This bot is ideal for group administrators who want to maintain control over chat content and user behavior.

## Features

- **Keyword Monitoring**: Automatically monitors messages for specified keywords and takes action when found.
- **User Management**: Temporarily mutes or bans users who use prohibited keywords.
- **Message Deletion**: Deletes specific messages or clears a number of recent messages from the chat.
- **Keyword Management**: Allows administrators to add, delete, and list keywords that the bot should monitor.

## Requirements

- Python 3.5+
- Telethon
- MySQL Database
- A Telegram bot token from [BotFather](https://t.me/BotFather)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/LiteeDev/TeleWatcher.git
   cd TeleWatcher
   ```
   
2. **Install the required Python packages**:
	  ```bash
		pip install -r requirements.txt
	```

3. **Configure the MySQL Database:**

	Create a MySQL database and run the following SQL commands to set up the required tables:

	```sql
	CREATE DATABASE tbl_tele_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 
	USE tbl_tele_bot; 

	CREATE TABLE `keywords` ( 
	`id` INT AUTO_INCREMENT PRIMARY KEY, 
	`keyword` VARCHAR(255) NOT NULL 
	); 

	CREATE TABLE `processed_messages` ( 
	`id` INT AUTO_INCREMENT PRIMARY KEY, 
	`message_id` BIGINT NOT NULL, 
	`chat_id` BIGINT NOT NULL, 
	`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ); 

	CREATE TABLE `messages` ( 
	`id` INT AUTO_INCREMENT PRIMARY KEY, 
	`message_id` BIGINT NOT NULL, 
	`user_id` BIGINT NOT NULL, 
	`chat_id` BIGINT NOT NULL, 
	`message_text` TEXT, 
	`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP );
	```


4. Edit the bot.py file and update the following configuration variables with your details:
	
	``` python
	db_config = {
	    'host': 'localhost',
	    'user': 'root',
	    'password': 'yourpassword',
	    'db': 'tbl_tele_bot',
	    'charset': 'utf8mb4',
	}

	bot_token = 'YOUR_BOT_TOKEN'  # Replace with your bot token
	api_id = 'YOUR_API_ID'  # Replace with your API ID
	api_hash = 'YOUR_API_HASH'  # Replace with your API hash
	mute_time_in_minutes =  10  # How long a muted user should be muted for.
	incident_report =  'mute'  # What we should do to the user.
	allowed_chat_ids = [-xxxxxx] # Replace with your chat IDs that you want to watch.
	```

	```
	Run the Bot:
	python bot.py
	```

	```
	Admin Commands (ONLY ADMINS OF THE CHAT CAN ACCESS THIS)
	.addKeyword <keyword>: Adds a keyword to the list of monitored keywords.
	.deleteKeyword <keyword>: Deletes a keyword from the list of monitored keywords.
	.listKeywords: Lists all keywords currently monitored by the bot.
	```
