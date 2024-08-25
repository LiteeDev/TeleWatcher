from telethon import TelegramClient, events, functions, types
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.functions.messages import DeleteMessagesRequest
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins
import re
import asyncio
import MySQLdb
from datetime import datetime, timedelta
import os

# Database configuration
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

# Initialize MySQL connection
def init_db():
    try:
        connection = MySQLdb.connect(**db_config)
        cursor = connection.cursor()
        print("Database connection established successfully.")
        return connection, cursor
    except MySQLdb.Error as e:
        print(f"Error connecting to the database: {e}")
        return None, None

# Check if a given message ID has already been processed
def is_message_processed(message_id, chat_id, cursor):
    try:
        query = "SELECT COUNT(*) FROM processed_messages WHERE message_id = %s AND chat_id = %s"
        cursor.execute(query, (message_id, chat_id))
        count = cursor.fetchone()[0]
        return count > 0
    except MySQLdb.Error as e:
        print(f"Error checking message processed status: {e}")
        return False

# Mark a message as processed
def mark_message_as_processed(message_id, chat_id, cursor, connection):
    try:
        query = "INSERT INTO processed_messages (message_id, chat_id) VALUES (%s, %s)"
        cursor.execute(query, (message_id, chat_id))
        connection.commit()
        print(f"Marked message {message_id} in chat {chat_id} as processed.")
    except MySQLdb.Error as e:
        print(f"Error marking message as processed: {e}")

# Check if a message contains any of the monitored keywords
def contains_keywords(text, cursor):
    try:
        query = "SELECT keyword FROM keywords"
        cursor.execute(query)
        keywords = cursor.fetchall()
        for keyword in keywords:
            if keyword[0].lower() in text.lower():
                print(f"Message contains monitored keyword: {keyword[0]}")
                return True
        return False
    except MySQLdb.Error as e:
        print(f"Error checking keywords: {e}")
        return False

# Mute or ban a user temporarily
async def mute_or_ban_user(client, channel, user_id, duration_minutes, action='mute'):
    try:
        # Fetch user and channel entities
        channel_entity = await client.get_input_entity(channel)  # Get InputChannel
        user_entity = await client.get_input_entity(user_id)  # Get InputUser
        user = await client.get_entity(user_entity)  # Get full User entity for display name
        username = user.username or user.first_name  # Use username if available, otherwise use first name

        until_date = datetime.utcnow() + timedelta(minutes=duration_minutes)
        rights = ChatBannedRights(
            until_date=until_date,
            send_messages=True
        )
        if action == 'ban':
            rights.view_messages = True

        print(f"Attempting to {'ban' if action == 'ban' else 'mute'} user {user_id} in channel {channel_entity} for {duration_minutes} minutes.")
        await client(EditBannedRequest(
            channel=channel_entity,
            participant=user_entity,
            banned_rights=rights
        ))
        print(f"User {user_id} has been {'banned' if action == 'ban' else 'muted'} successfully.")

        # Send a notification message to the channel
        mute_ban_message = f"User @{username} has been {'banned' if action == 'ban' else 'muted'} for {duration_minutes} minutes."
        await client.send_message(channel_entity, mute_ban_message)

    except Exception as e:
        print(f"Error muting or banning user: {e}")

# Delete a specific message
async def delete_message(client, channel, message_id):
    try:
        # Fetch channel entity
        channel_entity = await client.get_input_entity(channel)  # Get InputChannel

        print(f"Attempting to delete message {message_id} in channel {channel_entity}.")
        
        # Delete the message using delete_messages method
        result = await client(functions.channels.DeleteMessagesRequest(
            channel=channel_entity,
            id=[message_id]
        ))

        print(f"Delete result: {result}")
        print(f"Message {message_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting message: {e}")

# Clear chat messages
async def clear_chat_messages(client, channel, num_messages):
    try:
        # Fetch channel entity
        channel_entity = await client.get_input_entity(channel)  # Get InputChannel

        # Get the specified number of recent messages
        messages = await client.get_messages(channel_entity, limit=num_messages)
        message_ids = [msg.id for msg in messages]

        print(f"Attempting to delete {len(message_ids)} messages in channel {channel_entity}.")
        
        # Delete the messages using delete_messages method
        if message_ids:
            result = await client(functions.messages.DeleteMessagesRequest(
                id=message_ids
            ))

            print(f"Delete result: {result}")
            print(f"{len(message_ids)} messages deleted successfully.")
        else:
            print("No messages to delete.")
    except Exception as e:
        print(f"Error clearing chat messages: {e}")

# Add a keyword to the database
def add_keyword_to_db(keyword, cursor, connection):
    try:
        query = "INSERT INTO keywords (keyword) VALUES (%s)"
        cursor.execute(query, (keyword,))
        connection.commit()
        print(f"Keyword '{keyword}' added successfully.")
    except MySQLdb.Error as e:
        print(f"Error adding keyword to database: {e}")

# Delete a keyword from the database
def delete_keyword_from_db(keyword, cursor, connection):
    try:
        query = "DELETE FROM keywords WHERE keyword = %s"
        cursor.execute(query, (keyword,))
        connection.commit()
        print(f"Keyword '{keyword}' deleted successfully.")
    except MySQLdb.Error as e:
        print(f"Error deleting keyword from database: {e}")

# List all keywords from the database
def list_keywords(cursor):
    try:
        query = "SELECT keyword FROM keywords"
        cursor.execute(query)
        keywords = cursor.fetchall()
        return [keyword[0] for keyword in keywords]
    except MySQLdb.Error as e:
        print(f"Error fetching keywords from database: {e}")
        return []

# Check if a user is an admin
async def is_user_admin(client, chat_id, user_id):
    try:
        channel = await client.get_entity(chat_id)
        async for admin in client.iter_participants(channel, filter=ChannelParticipantsAdmins):
            if admin.id == user_id:
                print(f"User {user_id} is an admin in chat {chat_id}.")
                return True
        print(f"User {user_id} is NOT an admin in chat {chat_id}.")
    except Exception as e:
        print(f"Error checking admin rights for user {user_id} in chat {chat_id}: {e}")
    return False

async def main():
    session_name = 'test'

    # Create a new client instance for the bot
    client = TelegramClient(session_name, api_id, api_hash)

    async with client:
        await client.start(bot_token=bot_token)
        print("Bot started successfully.")

        connection, cursor = init_db()
        if not connection or not cursor:
            print("Failed to connect to the database. Exiting.")
            return

        # Register event handlers here, after the client is initialized
        @client.on(events.NewMessage(pattern=r'\.(addKeyword|deleteKeyword|listKeywords|clearChat)'))
        async def process_commands(event):
            message = event.message
            command_parts = message.text.split(' ', 1)
            command = command_parts[0].lower()

            if command == '.addkeyword':
                if await is_user_admin(client, message.chat_id, message.sender_id):
                    keyword = command_parts[1] if len(command_parts) > 1 else None
                    if keyword:
                        add_keyword_to_db(keyword.strip(), cursor, connection)
                        await message.reply(f"Keyword '{keyword}' has been added.")
                    else:
                        await message.reply("Please provide a keyword to add. Usage: .addKeyword <keyword>")
                else:
                    await message.reply("You do not have permission to use this command.")
            
            elif command == '.deletekeyword':
                if await is_user_admin(client, message.chat_id, message.sender_id):
                    keyword = command_parts[1] if len(command_parts) > 1 else None
                    if keyword:
                        delete_keyword_from_db(keyword.strip(), cursor, connection)
                        await message.reply(f"Keyword '{keyword}' has been deleted.")
                    else:
                        await message.reply("Please provide a keyword to delete. Usage: .deleteKeyword <keyword>")
                else:
                    await message.reply("You do not have permission to use this command.")
            
            elif command == '.listkeywords':
                if await is_user_admin(client, message.chat_id, message.sender_id):
                    keywords = list_keywords(cursor)
                    if keywords:
                        await message.reply(f"Keywords:" + "\n".join(keywords))
                    else:
                        await message.reply("No keywords found.")
                else:
                    await message.reply("You do not have permission to use this command.")

            elif command == '.clearchat':
                if await is_user_admin(client, message.chat_id, message.sender_id):
                    num_messages = int(command_parts[1]) if len(command_parts) > 1 and command_parts[1].isdigit() else 10
                    await clear_chat_messages(client, message.chat_id, num_messages)
                    await message.reply(f"Cleared {num_messages} messages.")
                else:
                    await message.reply("You do not have permission to use this command.")

        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            message = event.message
            group_id = event.chat_id

            # Check if the chat ID is in the allowed list
            if group_id not in allowed_chat_ids:
                return

            if not message.text:
                return

            # Check if the message has already been processed
            if is_message_processed(message.id, group_id, cursor):
                return

            print(f"Processing message ID {message.id} in chat {group_id}")

            # Mark the message as processed
            mark_message_as_processed(message.id, group_id, cursor, connection)

            # Check for monitored keywords in messages
            if contains_keywords(message.text, cursor):
                print(f"Flagged message in 'test dev' by {message.sender_id}")

                # Store flagged message in the database
                cursor.execute(
                    "INSERT INTO messages (message_id, user_id, chat_id, message_text) VALUES (%s, %s, %s, %s)",
                    (message.id, message.sender_id, group_id, message.text)
                )
                connection.commit()
                print(f"Stored flagged message ID {message.id} in database.")

                # Mute or ban the user temporarily
                await mute_or_ban_user(client, group_id, message.sender_id, duration_minutes=mute_time_in_minutes, action=incident_report)

                # Delete the message
                await delete_message(client, group_id, message.id)

        print("Bot is running...")
        await client.run_until_disconnected()

if __name__ == "__main__":
    # Use manual event loop for Python 3.6 or earlier
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
