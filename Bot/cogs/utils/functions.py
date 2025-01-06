# discord imports
import discord
from discord.ext import commands 

# python imports
from dotenv import load_dotenv
import os
import re

# 3rd party imports
import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection
import yt_dlp

# local imports
from logger import logger

load_dotenv()
DATABASE_ENDPOINT = os.getenv("DATABASE_ENDPOINT")
DATABASE_USER = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")


def load_ids() -> dict[int, dict[str, int]]:
    logger.debug("Loading IDs from the database.")
    # load the ids from the database
    connection = create_connection("Servers")
    query = "SELECT * FROM guilds"
    result = select_query(connection, query, [])
    if result:
        ids = {}
        for guild in result:
            server_id = guild["server_id"]
            ids[server_id] = {
                "owner_id": guild["owner_id"],
                "sancturary_keeper_role_id": guild["sancturary_keeper_role_id"],
                "sky_guardians_role_id": guild["sky_guardians_role_id"],
                "tech_oracle_role_id": guild["tech_oracle_role_id"],
                "event_luminary_role_id": guild["event_luminary_role_id"],
                "assistaint_role_id": guild["assistaint_role_id"],
                "support_category_id": guild["support_category_id"],
                "general_category_id": guild["general_category_id"],
                "music_voice_id": guild["music_voice_id"],
                "bot_channel_id": guild["bot_channel_id"],
                "music_channel_id": guild["music_channel_id"],
                "ticket_channel_id": guild["ticket_channel_id"],
                "ticket_log_channel_id": guild["ticket_log_channel_id"]
            }
        close_connection(connection)
        return ids
    logger.error("No IDs found in the database.")
    raise Exception("No IDs found in the database.")

# Function to send the response
async def send_message_to_user(client: commands.Bot, user_id: int, message: str) -> None:
    if not message:
        logger.debug("User message is empty.")
        return

    try:
        # Assuming get_response is defined in responses.py and returns a string
        user = client.get_user(user_id)
        await user.send(str(message))
    
    except Exception as e:
        logger.error(f"An error occurred while trying to send an message: {e}")


# Function to save the transcript of a ticket
async def save_transcript(channel: discord.TextChannel, ticket_logs: str) -> str:
    logger.info(f"Saving transcript for ticket {channel.name}")
    _dir = os.path.dirname(__file__)
    path = f"{_dir}/assets/tickets/ticket-{channel.name}.txt"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        # Open the file with UTF-8 encoding and handle any encoding errors gracefully
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            logger.info(f"Writing transcript for ticket {channel.name}")
            async for message in channel.history(limit=None):
                # Append the message with the author's name to the logs
                ticket_logs = f"{message.author.name}: {message.content}\n" + ticket_logs
            ticket_logs = f"Transcript for {channel.name}:\n" + "```\n" + ticket_logs + "```"
            f.write(ticket_logs)
        return path
    except Exception as e:
        logger.critical(f"Error saving transcript for {channel.name}: {e}")


# Function to create MySQL database connection
def create_connection(database_name: str) -> mysql.connector.connection.MySQLConnection:
    logger.debug(f"Connecting to the database: {database_name}")
    connection = None
    try:
        connection: PooledMySQLConnection | MySQLConnectionAbstract = mysql.connector.connect(
            host=DATABASE_ENDPOINT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=database_name,
            port=DATABASE_PORT
        )
        if not connection.is_connected():
            logger.error("Failed to connect to the database.", extra={
                "host": DATABASE_ENDPOINT,
                "user": DATABASE_USER,
                "database": database_name,
                "port": DATABASE_PORT
            })
    except Error as e:
        logger.error(f"The error '{e}' occurred")
    return connection


# Insert query function
def insert_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    logger.debug(f"Inserting data into the database: {values}")
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Select query function
def select_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values=None):
    logger.debug(f"Selecting data from the database: {query}")
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, values)
        result = cursor.fetchall()
        return result
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Update query function
def update_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    logger.debug(f"Updating data in the database: {values}")
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")

# Delete query function
def delete_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    logger.debug(f"Deleting data from the database: {values}")
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Close MySQL connection
def close_connection(connection: PooledMySQLConnection | MySQLConnectionAbstract):
    if connection.is_connected():
        logger.debug("Closing the database connection.")
        connection.close()
    if connection.is_connected():
        logger.error("Failed to close the database connection.")
    else:
        logger.debug("Database connection closed.")


def get_guildSettings(connection: PooledMySQLConnection | MySQLConnectionAbstract, guild_id: int):
    logger.debug(f"Getting guild settings from the database: {guild_id}")
    query = "SELECT * FROM guilds WHERE server_id = %s"
    result = select_query(connection, query, (guild_id,))
    if result:
        return result[0]
    logger.warning(f"No guild settings found in the database for guild {guild_id}")
    return None


def set_guildSettings(connection: PooledMySQLConnection | MySQLConnectionAbstract, guild_id: int, owner_id: int, sancturary_keeper_role_id: int, sky_guardians_role_id: int, tech_oracle_role_id: int, event_luminary_role_id: int, assistaint_role_id: int, support_category_id: int, general_category_id: int, music_voice_id: int, bot_channel_id: int, music_channel_id: int, ticket_channel_id: int, ticket_log_channel_id: int):
    logger.info(f"Setting guild settings in the database: {guild_id}")
    query = "INSERT INTO guilds (server_id, owner_id, sancturary_keeper_role_id, sky_guardians_role_id, tech_oracle_role_id, event_luminary_role_id, assistaint_role_id, support_category_id, general_category_id, music_voice_id, bot_channel_id, music_channel_id, ticket_channel_id, ticket_log_channel_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (guild_id, owner_id, sancturary_keeper_role_id, sky_guardians_role_id, tech_oracle_role_id, event_luminary_role_id, assistaint_role_id, support_category_id, general_category_id, music_voice_id, bot_channel_id, music_channel_id, ticket_channel_id, ticket_log_channel_id)
    insert_query(connection, query, values)
    


def save_ticket_to_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, user_id: int, channel_id: int):
    logger.info(f"Saving ticket to the database: {user_id}, {channel_id}")
    query = "INSERT INTO open_tickets (user_id, channel_id) VALUES (%s, %s)"
    values = (user_id, channel_id)
    insert_query(connection, query, values)


def load_ticket_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int):
    logger.debug(f"Loading ticket from the database: {channel_id}")
    query = "SELECT user_id FROM open_tickets WHERE channel_id = %s"
    result = select_query(connection, query, (channel_id,))
    if result:
        return result[0]  # Return the first matching ticket record
    logger.warning(f"No ticket found in the database for channel {channel_id}")
    return None


def delete_ticket_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int):
    logger.debug(f"Deleting ticket from the database: {channel_id}")
    query = "DELETE FROM open_tickets WHERE channel_id = %s"
    delete_query(connection, query, (channel_id,))


def get_rule_channels(connection: PooledMySQLConnection | MySQLConnectionAbstract):
    logger.debug("Getting rule channels from the database.")
    query = "SELECT * FROM rule_channels"
    result = select_query(connection, query)
    if result:
        return result
    logger.info("No rule channels found in the database.")
    return None

def get_rule_channel(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int):
    logger.debug(f"Getting rule channel from the database: {channel_id}")
    query = "SELECT * FROM rule_channels WHERE channel_id = %s"
    result = select_query(connection, query, (channel_id,))
    if result:
        return result
    logger.info(f"No rule channel found in the database for channel {channel_id}")
    return None

def create_rule_channel(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int,  creator_id: int):
    logger.info(f"Creating rule channel in the database: {channel_id}, {creator_id}")
    query = "INSERT INTO rule_channels (channel_id, creator_id) VALUES (%s, %s)"
    values = (channel_id, creator_id)
    insert_query(connection, query, values)

def remove_rule_channel(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int):
    logger.info(f"Removing rule channel from the database: {channel_id}")
    query = "DELETE FROM rule_channels WHERE channel_id = %s"
    delete_query(connection, query, (channel_id,))
    query = "DELETE FROM rules_accepted WHERE channel_id = %s"
    delete_query(connection, query, (channel_id,))

def set_accepted_rules(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int, user_id: int):
    logger.info(f"Setting accepted rules in the database: {channel_id}, {user_id}")
    query = "INSERT INTO rules_accepted (channel_id, user_id) VALUES (%s, %s)"
    values = (channel_id, user_id)
    insert_query(connection, query, values)

def get_accepted_rules(connection: PooledMySQLConnection | MySQLConnectionAbstract, channel_id: int):
    logger.debug(f"Getting accepted rules from the database: {channel_id}")
    query = "SELECT * FROM rules_accepted WHERE channel_id = %s"
    result = select_query(connection, query, (channel_id,))
    if result:
        return result
    logger.info(f"No accepted rules found in the database for channel {channel_id}")
    return None


# Function to get the video URLs from a playlist
def get_video_urls_from_playlist(playlist_url):
    logger.debug(f"Getting video URLs from the playlist: {playlist_url}")
    ydl_opts: dict[str, bool] = {
        'extract_flat': True,  # Only extract the URL, no downloads
        'quiet': True  # Suppress output
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(playlist_url, download=False)
            video_urls = [entry['url'] for entry in info_dict['entries']]
            playlist_title = info_dict['title']
            return video_urls, playlist_title
        except Exception as e:
            logger.error(f"An error occurred while trying to fetch the video URLs: {e}")
            return []


# Main function
def get_video_urls(url: str) -> list|str:
    logger.debug(f"Getting video URLs from the URL: {url}")
    playlist_pattern = r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+'
    radio_pattern = r"^https?:\/\/(www\.)?youtube\.com\/.*[?&]list=(RD|RDEM)[^&]+.*"
    video_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+'

    if re.match(playlist_pattern, url):
        video_urls, _ = get_video_urls_from_playlist(url)
        if not video_urls:
            logger.warning("No video URLs found in the playlist.")
            return []
        return video_urls

    elif re.match(radio_pattern, url):
        logger.debug("The provided URL is a radio URL.")
        return "radio"

    elif re.match(video_pattern, url):
        logger.debug("The provided URL is a video URL.")
        return [url]

    else:
        logger.debug("The provided URL is not a valid YouTube URL.")
        return []