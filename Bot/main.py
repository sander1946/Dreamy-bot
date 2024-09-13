# discord imports
from discord.ext import commands
from discord import app_commands
import discord
import discord.ui

# python imports 
from dotenv import load_dotenv
from typing import Final
import asyncio
import time
import os
import json


# local imports
from functions import load_ids, save_transcript, get_video_urls
from ticketMenu import PersistentTicketView, PersistentCloseTicketView

# 3rd party imports
import yt_dlp


# Load the environment variables
load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
TESTING: Final[str] = os.getenv("TESTING")
bot_prefix: Final[str] = os.getenv("PREFIX")
YOUTUBE_PASSWORD: Final[str] = os.getenv("YOUTUBE_PASSWORD")

# Load the IDs from the database
ids = load_ids()

# team settings
max_teams: int = 4
cooldown_period: int = 60

# music settings
yt_dlp_options: dict[str, str] = {"username": "oauth2", "password": YOUTUBE_PASSWORD, "format": "bestaudio/best", 'noplaylist': False, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
ffmpeg_options: dict[str, str] = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

# youtube variables
youtube_base_url: str = 'https://www.youtube.com/'
youtube_results_url: str = youtube_base_url + 'results?'
youtube_watch_url: str = youtube_base_url + 'watch?v='
ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(yt_dlp_options)

# Initialize the dictionaries and lists
teams: dict = {}
update_queue: list = []
full_team_cooldowns: dict = {}
voice_clients: dict[int, discord.VoiceChannel] = {}
queues: dict = {}
reaction_tracker: dict = {}

# Create a bot instance
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)


# load the command whitelist
dir = os.path.dirname(__file__)
with open(f"{dir}/whitelist.json", "r") as file:
    command_whitelist = json.load(file)["no_error_commands"]


# Startup of the bot
@client.event
async def on_ready() -> None:
    print(f"\n\n[info] Bot is ready as {client.user}\n")
    
    client.add_view(PersistentTicketView(client))
    client.add_view(PersistentCloseTicketView(client))
    
    # Set Rich Presence (Streaming)
    if TESTING == "True":
        # Under Development (Do not disturb)
        activity = discord.Activity(type=discord.ActivityType.playing, name="Do not disturb, im getting tested")
        await client.change_presence(status=discord.Status.do_not_disturb, activity=activity)
    else:
        # Streaming PixelPoppyTV (streaming)
        activity = discord.Activity(type=discord.ActivityType.streaming, name="PixelPoppyTV", url="https://www.twitch.tv/pixelpoppytv", details="PixelPoppyTV", state="Sky: Children of The Light")
        await client.change_presence(status=discord.Status.online, activity=activity)
    
    await client.tree.sync()  # Sync slash commands


@client.tree.command(name="help", description="Lists all available commands.")
async def help_command(interaction: discord.Interaction):
    # Create an embed for displaying the commands
    embed = discord.Embed(title="Dreamy Commands 🍃", description="Here is everything I can do for you!", color=discord.Color.green())
    embed.set_image(url="https://i.postimg.cc/28LPZLBW/20240821214134-1.jpg")
    # Loop through all commands in the CommandTree and add them to the embed
    for command in client.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=f"```{command.description}```", inline=False)
        
    # Send the embed to the user
    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command(name="ping", description="Check the bot's current latency.")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Pong! that took me {round(client.latency * 1000)}ms to respond")
    print(f"[info] {interaction.user.name} requested the bot's latency, it's {round(client.latency * 1000)}ms")

# ticket commands
@client.tree.command(name="ticket_menu", description="Create a ticket create menu.")
async def ticket(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.followup.send("```fix\nYou do not have permission to create a ticket menu.```", ephemeral=True)
        return
    await interaction.followup.send(
        "How to Submit Tickets:\n\n1. Click the button below to create a ticket.\n2. Choose the type of ticket you would like to create.\n3. A ticket channel will be created for you.\n4. Give as much detail as possible about the issue or question.\n5. Wait for response.\n6. Close ticket when response has been received.\n\n**Tickets remain saved on our side, so when you close a ticket we are still able to review the ticket and delete it afterwards.**", 
        view=PersistentTicketView(client))


@client.tree.command(name="force_close_ticket", description="Force close a ticket. This will CLOSE ANY channel and send the logs to the log channel.")
async def force_close_ticket(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    sky_guardians_role = interaction.guild.get_role(ids[interaction.guild.id]["sky_guardians_role_id"])
    if not sky_guardians_role:
        print("[error][tickets] Sky Guardians role not found. Please provide a valid role ID.")
        await interaction.followup.send("```fix\nSky Guardians role not found. Please provide a valid role ID.```", ephemeral=True)
        return
    
    tech_oracle_role = interaction.guild.get_role(ids[interaction.guild.id]["tech_oracle_role_id"])
    if not tech_oracle_role:
        print("[error][tickets] Tech Oracle role not found. Please provide a valid role ID.")
        await interaction.followup.send("```fix\nTech Oracle role not found. Please provide a valid role ID.```", ephemeral=True)
        return
    
    if interaction.user.id != ids[interaction.guild.id]["owner_id"] or sky_guardians_role in interaction.user.roles or tech_oracle_role in interaction.user.roles:
        await interaction.followup.send("Ticket will be force closed.")

        ticket_logs = ""
        path = await save_transcript(interaction.channel, ticket_logs)

        ticket_logs_channel = client.get_channel(ids[interaction.guild.id]["ticket_log_channel_id"])
        if ticket_logs_channel:
            await ticket_logs_channel.send(f"Transcript for {interaction.channel.name}:", file=discord.File(path))
        else:
            print("[warning][tickets] Ticket logs channel not found. Please provide a valid channel name.")
        print(f"[tickets] Ticket closed by user {interaction.user.name} in channel {interaction.channel.name}")
        await interaction.channel.delete()
        await interaction.user.send("Your ticket has been closed successfully. The Transcript of the ticket has been saved.")
        await interaction.user.send(f"Transcript for {interaction.channel.name}:", file=discord.File(path))
    else:
        print(f"[warning][tickets] {interaction.user.name} does not have prems to close ticket {interaction.channel.name}")
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)


# info commands
@client.tree.command(name="timers", description="Gives the link to all of the timers.")
async def timers(interaction: discord.Interaction) -> None:
    timer_channel_url = "https://discord.com/channels/1239651599480127649/1252324353115291849/1252324488901824556"
    response = "Here is the url to the channel with all the timers:\n" + timer_channel_url
    print(f"[info] {interaction.user.name} requested the timer")
    await interaction.response.send_message(response)
    

# Team commands
@client.tree.command(name="createteam", description="Create a team with a leader and an emoji.")
async def createteam(interaction: discord.Interaction, member: discord.Member, emoji: str) -> None:
    await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
    allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.followup.send("You do not have permission to create a team.", ephemeral=True)
        return
    
    if member.id in teams:
        await interaction.followup.send("This user already leads a team.", ephemeral=True)
        return

    if len(teams) >= max_teams:
        await interaction.followup.send("The maximum number of teams has been reached. Cannot create a new team.", ephemeral=True)
        return
    
    emoji = emoji.strip(":")  # Remove the colons from the emoji if present
    print(f"[teams] Creating a team with {member.name}:{member.id} as the leader and {emoji} as the emoji.")
    
    await interaction.followup.send(f"Team {emoji} has been created!", ephemeral=False)
    team_message = f"__**Group Leader**__\n{member.mention} {emoji}\n\n__**Members**__\n"

    message = await interaction.channel.send(team_message)

    # Add the bot's reaction
    await message.add_reaction(emoji)

    # Save team information
    teams[member.id] = {
        "message_id": message.id,
        "emoji": emoji,
        "members": [],
        "max_members": 8,  # Max members in the team
        "leader_id": member.id,
        "reaction_count": 1,  # Start with 1 to count the team leader
        "last_locked_message_time": 0,
        "locked": False,  # Initialize the locked state
        "channel_id": interaction.channel.id,  # Track the channel ID
        "resetting": False  # Track if the team is currently resetting
    }


@client.tree.command(name="closeteam", description="Close the given leader's team.")
async def closeteam(interaction: discord.Interaction, member: discord.Member) -> None:
    await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
    allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.followup.send("You do not have permission to close a team.", ephemeral=True)
        return
    
    if member.id not in teams:
        await interaction.followup.send(f"A team led by {member.mention} not found.", ephemeral=True)
        return
    
    team_data = teams[member.id]
    
    # Check if the team is locked
    if team_data["locked"] == False: 
        await interaction.followup.send(f"Team {team_data['emoji']} led by {member.mention} is not currently locked. Please lock the team first.", ephemeral=True)
        return
    team_data["closed"] = True  # Set the closed flag
    channel = client.get_channel(team_data["channel_id"])  # Get the team's channel
    message = await channel.fetch_message(team_data["message_id"])  # Fetch the message
    await message.delete()  # Delete the message

    del teams[member.id]  # Remove the team from the dictionary
    await interaction.channel.send(f"Team {team_data['emoji']} led by {member.mention} has been closed.")
    await interaction.followup.send(f"Team {team_data['emoji']} led by {member.mention} has been closed.", ephemeral=False)


@client.tree.command(name="lockteam", description="Lock the given leader's team.")
async def lockteam(interaction: discord.Interaction, member: discord.Member) -> None:
    await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
    allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.followup.send("You do not have permission to lock a team.", ephemeral=True)
        return
        
    if member.id not in teams:
        await interaction.followup.send(f"A team led by {member.mention} not found.", ephemeral=True)
        return
        
    team_data = teams[member.id]
    message_id = team_data["message_id"]
    
    if team_data["locked"] == True: 
        await interaction.followup.send(f"Team {team_data['emoji']} is already locked.", ephemeral=True)
        return
    
    # Retrieve the team message
    message = await interaction.channel.fetch_message(message_id)
    
    # Update the message to indicate the team is locked
    updated_message = message.content + "\n\n__**Team Full**__ - This team has been locked ^^"
    update_queue.append((message_id, updated_message))

    # Set the locked flag for the team
    teams[member.id]["locked"] = True
    await interaction.followup.send(f"Team {team_data['emoji']} has been locked.", ephemeral=False)
    await interaction.channel.send(f"Team {team_data['emoji']} has been locked.")


@client.tree.command(name="unlockteam", description="Unlock a given leader's team.")
async def unlockteam(interaction: discord.Interaction, member: discord.Member) -> None:
    await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
    allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.followup.send("You do not have permission to unlock a team.", ephemeral=True)
        return
    
    if member.id not in teams:
        await interaction.followup.send(f"A team led by {member.mention} not found.", ephemeral=True)
        return
    
    team_data = teams[member.id]
    message_id = team_data["message_id"]

    if team_data["locked"] == False:
        await interaction.followup.send("Team is not locked.", ephemeral=True)
        return

    # Prevent modifications during the reset phase
    teams[member.id]["resetting"] = True

    # Retrieve the team message
    message = await interaction.channel.fetch_message(message_id)

    # Update the message to indicate the reset procedure
    reset_message = f"__**Group Leader**__\n{client.get_user(team_data['leader_id']).mention} :{team_data['emoji']}:\n\n__**Members**__\n<> The bot is currently resetting the player list. Please wait. <>"
    await message.edit(content=reset_message)
    
    wait_message = await interaction.channel.send("Please wait for the team to unlock...")
    await interaction.followup.send(f"Team {team_data['emoji']} will be unlocked", ephemeral=True)

    # Adding a delay to simulate the refresh time
    await asyncio.sleep(2)

    # Rebuild the team members list based on the reaction order
    if member.id in reaction_tracker:
        # Sort the users based on the timestamp of when they reacted
        sorted_reactors = sorted(reaction_tracker[member.id], key=lambda x: x["timestamp"])

        team_data["members"] = []  # Start with an empty list
        for reactor in sorted_reactors:
            if len(team_data["members"]) < team_data["max_members"]:
                team_data["members"].append(reactor["user_id"])
                print(f"[teams] Added user {reactor['user_id']} to team {team_data['leader_id']} after unlocking.")
        
        # Inform the channel if the team is full again
        if len(team_data["members"]) >= team_data["max_members"]:
            teams[member.id]["locked"] = True

        # Update the team message to reflect the current state
        member_mentions = [
            client.get_user(member_id).mention for member_id in team_data["members"] if member_id != team_data["leader_id"]
        ]
        member_names_str = "\n".join(member_mentions)
        final_message = f"__**Group Leader**__\n{client.get_user(team_data['leader_id']).mention} :{team_data['emoji']}:\n\n__**Members**__\n<*> Fixing the member list UwU <*>"

        if member_names_str:
            final_message += f"\n\n{member_names_str}"
        await message.edit(content=final_message)

    # Remove resetting status and unlock the team
    teams[member.id]["resetting"] = False
    teams[member.id]["locked"] = False
    
    await interaction.channel.send(f"Team {team_data['emoji']} has been unlocked.")

    await wait_message.delete()


# Music commands
@client.tree.command(name="play", description="Play a YouTube song or playlist from a URL.")
async def play(interaction: discord.Interaction, url: str) -> None:
    await interaction.response.defer()  # Defer to allow time for processing
    guild_id = interaction.guild.id

    # Specify the channel ID or name you want the bot to join
    # You can use the channel ID directly for accuracy, or fetch it by name
    music_channel = discord.utils.get(interaction.guild.voice_channels, id=ids[guild_id]["music_voice_id"])

    if music_channel is None:
        await interaction.followup.send("```fix\nThe specified voice channel does not exist. please update the channel ID.```")
        return
    
    if client.voice_clients and guild_id in voice_clients:
        voice_client = voice_clients[guild_id]
    else:
        try:
            # Connect to the specific voice channel
            voice_client = await music_channel.connect()
            voice_clients[guild_id] = voice_client
        except TypeError as e:
            print(f"[error][player] Error connecting to the voice channel: {e}")
            await interaction.followup.send("```fix\nAn error occurred while trying to connect to the voice channel.```")
            return

    # Get video or playlist URLs
    video_urls = get_video_urls(url)
    if video_urls == []:
        await interaction.followup.send("```fix\nInvalid URL or no video(s) were found.```")
        return
    if video_urls == "radio":
        await interaction.followup.send("```fix\nThis is a radio URL and cannot be processed.")
        return

    # If there's no queue for this guild, create one
    if guild_id not in queues:
        queues[guild_id] = []

    # If the bot is not already playing music, play the first song in the queue
    if not voice_clients[guild_id].is_playing():
        # Add video URLs to the queue
        queues[guild_id].extend(video_urls)
        await interaction.followup.send("Now playing in the music channel.")
        await play_next(interaction)
    else:
        # Add video URLs infront of the queue
        queues[guild_id] = [*video_urls, *queues[guild_id]]
        voice_client.stop()
        await interaction.followup.send(f"Added {len(video_urls)} to the front of the queue.")


@client.tree.command(name="queue", description="Queue the next song or playlist from a YouTube URL.")
async def queue(interaction: discord.Interaction, url: str) -> None:
    guild_id = interaction.guild.id
    
    # Get video or playlist URLs
    video_urls = get_video_urls(url)
    if not video_urls:
        await interaction.response.send_message("```fix\nInvalid URL or no videos found.```")
        return

    # If there's no queue for this guild, create one
    if guild_id not in queues:
        queues[guild_id] = []
    
    # Add the video(s) to the queue
    queues[guild_id].extend(video_urls)
    await interaction.response.send_message(f"Added {len(video_urls)} song(s) to the queue.")
    
    # If nothing is currently playing, play the first song in the queue
    if not voice_clients[guild_id].is_playing():
        await play_next(interaction)


@client.tree.command(name="clear_queue", description="Clear the current queue.")
async def clear_queue(interaction: discord.Interaction) -> None:
    if interaction.guild.id in queues:
        queues[interaction.guild.id].clear()
        await interaction.response.send_message("Queue cleared!")
    else:
        await interaction.response.send_message("There is no queue to clear")


@client.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction) -> None:
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused the song.")
        else:
            await interaction.response.send_message("No song is currently playing.")
    except Exception as e:
        print(f"[error][player] Error pausing the song: {e}")
        await interaction.response.send_message(f"```fix\nI'm unable to pause the song at the moment```")


@client.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction) -> None:
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed the song.")
        else:
            await interaction.response.send_message("No song is currently paused.")
    except Exception as e:
        print(f"[error][player] Error resuming the song: {e}")
        await interaction.response.send_message(f"```fix\nI'm unable to resume the song at the moment```")


@client.tree.command(name="skip", description="Skip the currently playing song.")
async def skip(interaction: discord.Interaction) -> None:
    guild_id = interaction.guild.id
    
    # Get the voice client for the guild
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    try:
        if voice_client and voice_client.is_playing():
            # Stop the current song
            voice_client.stop()

            # Inform the user that the song was skipped
            await interaction.response.send_message("Skipped the song.")
        else:
            await interaction.response.send_message("No song is currently playing.")
    except Exception as e:
        print(f"[error][player] Error skipping the song: {e}")
        await interaction.response.send_message(f"```fix\nI'm unable to skip the song at the moment```")


@client.tree.command(name="stop", description="Stop the currently playing song and disconnect.")
async def stop(interaction: discord.Interaction) -> None:
    try:
        guild_id = interaction.guild_id
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        if voice_client:
            queues[guild_id] = []  # Clear the queue
            voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("Stopped the song and disconnected.")
        else:
            await interaction.response.send_message("No song is currently playing.")
    except Exception as e:
        print(f"[error][player] Error stopping the song: {e}")
        await interaction.response.send_message(f"```fix\nI'm unable to stop the song at the moment```")


# player functions for music
async def play_next(interaction: discord.Interaction) -> None:
    guild_id = interaction.guild.id
    music_spam_channel = client.get_channel(ids[guild_id]["music_channel_id"])
    # Check if there are songs in the queue
    if guild_id in queues and queues[guild_id]:
        next_url = queues[guild_id].pop(0)  # Get the next song from the queue
        loop = asyncio.get_event_loop()

        try:
            # Extract song info
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(next_url, download=False))
            song_url = data['url']
            player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

            # Play the song and set the after callback to play the next song in the queue
            voice_clients[guild_id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), client.loop))

            await music_spam_channel.send(f"Now playing: **{data['title']}**")
        except yt_dlp.DownloadError as e:
            print(f"[error][play_next] Error downloading the song: {e}")
            await music_spam_channel.send(f"```fix\nAn error occurred while trying to download the song. Skipping to the next song.```")
            await play_next(interaction)  # Automatically attempt to play the next song
        except Exception as e:
            print(f"[error][play_next] Error playing the song: {e}")
            await music_spam_channel.send(f"```fix\nAn error occurred while trying to play the song. Skipping to the next song.```")

            # If an error occurs, skip to the next song
            await play_next(interaction)  # Automatically attempt to play the next song
    else:
        # No more songs in the queue
        await music_spam_channel.send("The queue is empty, no more songs to play.")


# Reaction handling for team creation
@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    message_id = payload.message_id
    user_id = payload.user_id

    for team_id, team in teams.items():
        if message_id == team["message_id"]:
            emoji = payload.emoji.name

            if user_id != client.user.id and emoji == team["emoji"]:
                team_leader_id = team["leader_id"]
                print(f"[teams] User {user_id} reacted with {emoji} to team {team_leader_id}")
                channel = client.get_channel(payload.channel_id)

                # Skip updating members list if team is resetting
                if team["resetting"]:
                    return
                
                # Skip updating members list if team is locked
                if team["locked"]: 
                    return

                user = await client.fetch_user(user_id)  # Fetch the user who reacted

                if user_id != team_leader_id:
                    if user_id not in team["members"]:  # Only add if not already in the team
                        team["reaction_count"] += 1

                        # Track the reaction order
                        if team_id not in reaction_tracker:
                            reaction_tracker[team_id] = []
                        if not any(entry['user_id'] == user_id for entry in reaction_tracker[team_id]):
                            reaction_tracker[team_id].append({"user_id": user_id, "timestamp": time.time()})

                        # Check if team is full and not locked yet
                        if len(team["members"]) + 1 < team["max_members"]:
                            team["members"].append(user_id)  # Add member to the list
                            print(f"[teams] Added user {user_id} to team {team_leader_id}")
                            print(f"this team now has {len(team['members']) + 1} members including the leader")
                            print(team["members"])
                        else:
                            # If team is full, apply cooldown
                            team_leader = client.get_user(team_leader_id)
                            if team_leader is not None:
                                if team_leader_id not in full_team_cooldowns or time.time() - full_team_cooldowns[team_leader_id] > cooldown_period:
                                    await channel.send(
                                        f"The team of {team_leader.mention} :{team['emoji']}:\n"
                                        f"is full - Consider joining another team! {user.mention}"
                                    )
                                    full_team_cooldowns[team_leader_id] = time.time()
                            else:
                                print(f"[teams] Could not find user with ID {team_leader_id}")
                            return  # Do not add user if team is full

                        # Update the team message
                        member_mentions = []
                        for member_id in team["members"]:
                            try:
                                member = await client.fetch_user(member_id)  # Fetch the user from the Discord API
                                member_mentions.append(member.mention)
                            except discord.NotFound:
                                # Handle the case where the user cannot be found
                                print(f"[teams] User with ID {member_id} not found.")
                            except Exception as e:
                                print(f"[teams] An error occurred while fetching user {member_id}: {e}")

                        member_names_str = "\n".join(member_mentions)

                        # Safely get the team leader user and handle the case where it might return None
                        try:
                            team_leader = await client.fetch_user(team_leader_id)
                        except discord.NotFound:
                            print(f"[teams] Team leader with ID {team_leader_id} not found.")
                            team_leader = None
                        except Exception as e:
                            print(f"[teams] An error occurred while fetching team leader {team_leader_id}: {e}")
                            team_leader = None

                        if team_leader is not None:
                            updated_message = (
                                f"__**Group Leader**__\n{team_leader.mention} :{team['emoji']}:\n\n"
                                f"__**Members**__\n{member_names_str}"
                            )
                        else:
                            print(f"[teams] Could not find user with ID {team_leader_id}")
                            updated_message = (
                                f"__**Group Leader**__\n(Unknown user) :{team['emoji']}:\n\n"
                                f"__**Members**__\n{member_names_str}"
                            )

                        # Update the message
                        message = await channel.fetch_message(message_id)
                        print(f"[teams] Updating message {message_id}")
                        await message.edit(content=updated_message)

                        # Lock the team if it's full
                        if len(team["members"]) + 1 >= team["max_members"]:
                            team["locked"] = True
                            await channel.send(f"{client.get_user(team_leader_id).mention} group is now locked!")

                    else:
                        # User is already in the team
                        team["reaction_count"] -= 1


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent) -> None:
    message_id = payload.message_id
    user_id = payload.user_id

    for team_id, team in teams.items():
        if message_id == team["message_id"] and user_id in team["members"]:
            # Skip updating members list if team is resetting
            if team["resetting"] == True:
                return
            
            # Skip updating members list if team is locked
            if team["locked"] == True: 
                return
            
            team["members"].remove(user_id)  # Remove member from the list
            print(f"[teams] Removed user {user_id} from team {team_id}")

            # Update the message
            member_mentions = []
            for member_id in team["members"]:
                if member_id != team["leader_id"]:
                    try:
                        member = await client.fetch_user(member_id)
                        member_mentions.append(member.mention)
                    except discord.NotFound:
                        # Handle the case where the user cannot be found
                        print(f"[teams] User with ID {member_id} not found.")
                    except Exception as e:
                        print(f"[teams] An error occurred while fetching user {member_id}: {e}")
                        
            member_names_str = "\n".join(member_mentions)
            updated_message = (
                f"__**Group Leader**__\n{client.get_user(team['leader_id']).mention} :{team['emoji']}:\n\n"
                f"__**Members**__\n{member_names_str}"
            )

            # Add update to queue
            try:
                # Find the channel from the message ID
                for team in teams.values():
                    if message_id == team["message_id"]:
                        channel_id = team["channel_id"]
                        break
                else:
                    # If we do not find the message ID in our tracked teams, skip processing
                    continue

                channel = client.get_channel(channel_id)
                message = await channel.fetch_message(message_id)
                await message.edit(content=updated_message)
                print(f"[teams] Updated message {message_id}")
            except Exception as e:
                print(f"[teams] Failed to update message {message_id}: {e}")


# Error handling for command not found
@client.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        command = ctx.message.content.lower().strip(bot_prefix)
        if command in command_whitelist:
            print(f"[info] {ctx.author} tried to use an whitelisted command in channel {ctx.channel}: {ctx.message.content}")
            return
        print(f"[warning] {ctx.author} tried to use an unknown command in channel {ctx.channel}: {ctx.message.content}")
        # await ctx.send(f"Command not found! Please check your command or use `/help` for available commands.")
        await ctx.reply("Command not found! Please check your command or use `/help` for available commands.", ephemeral=True, delete_after=10)
        await ctx.message.delete(delay=10)
    else:
        # Raise the error if it's not CommandNotFound
        raise error


def main() -> None:
    client.run(TOKEN)


if __name__ == "__main__":
    main()