from __future__ import annotations

# discord imports
import discord
from discord.ext import commands

# python imports
import typing
import asyncio
import traceback
from dotenv import load_dotenv
import os

# local imports
from cogs.utils.BaseModal import BaseModal
from functions import load_ids, get_video_urls
from logger import logger

# 3rd party imports
import yt_dlp

load_dotenv()
# YOUTUBE_PASSWORD: typing.Final[str] = os.getenv("YOUTUBE_PASSWORD")


voice_clients: dict[int, discord.VoiceChannel] = {}
queues: dict[int, dict[str, str]] = {}


ids = load_ids()

# music settings
yt_dlp_options: dict[str, str] = {"username": "oauth2 ", "password ": '', "format": "bestaudio/best", 'noplaylist': False, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
ffmpeg_options: dict[str, str] = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

# youtube variables
youtube_base_url: str = 'https://www.youtube.com/'
youtube_results_url: str = youtube_base_url + 'results?'
youtube_watch_url: str = youtube_base_url + 'watch?v='
ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(yt_dlp_options)


class PersistentMusicView(discord.ui.View):
    def __init__(self, client: commands.Bot):
        super().__init__(timeout=None)  
        self.add_item(discord.ui.Button(emoji="<:Back:1306675066456772608>", style=discord.ButtonStyle.primary, custom_id="back", row=1))
        self.children[-1].callback = self.back_callback
        self.add_item(discord.ui.Button(emoji="<:Play:1306675076183359599>", style=discord.ButtonStyle.primary, custom_id="resume", row=1))
        self.children[-1].callback = self.pause_resume_callback
        self.add_item(discord.ui.Button(emoji="<:Skip:1306675079811301397>", style=discord.ButtonStyle.success, custom_id="skip", row=1))
        self.children[-1].callback = self.skip_callback
        self.add_item(discord.ui.Button(emoji="<:Queue:1306675077798039705>", style=discord.ButtonStyle.secondary, custom_id="queue", row=2))
        self.children[-1].callback = self.queue_callback
        self.add_item(discord.ui.Button(emoji="<:Clear_Queue:1306675068931149915>", style=discord.ButtonStyle.secondary, custom_id="clear_queue", row=2))
        self.children[-1].callback = self.clear_queue_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1306675070848204820>", style=discord.ButtonStyle.danger, custom_id="stop", row=2))
        self.children[-1].callback = self.stop_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1306675070848204820>", style=discord.ButtonStyle.secondary, disabled=True, custom_id="loop", row=3))
        self.children[-1].callback = self.loop_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1306675070848204820>", style=discord.ButtonStyle.secondary, disabled=True, custom_id="shuffle", row=3))
        self.children[-1].callback = self.shuffle_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1306675070848204820>", style=discord.ButtonStyle.secondary, disabled=True, custom_id="volume_up", row=3))
        self.children[-1].callback = self.volume_up_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1306675070848204820>", style=discord.ButtonStyle.secondary, disabled=True, custom_id="volume_down", row=3))
        self.children[-1].callback = self.volume_down_callback
        self.client = client
    
    async def back_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "back_callback"})
        guild_id = interaction.guild.id
    
        # Get the voice client for the guild
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        try:
            if voice_client and voice_client.is_playing():
                current_song = queues[guild_id]["current"]["original_url"] if queues[guild_id]["current"] else None
                previous_url = queues[guild_id]["played"].pop(-1) if queues[guild_id]["played"] else None
                if not current_song and previous_url:
                    queues[guild_id]["queue"] = [previous_url, *queues[guild_id]["queue"]]
                if previous_url and current_song:
                    queues[guild_id]["queue"] = [previous_url, current_song, *queues[guild_id]["queue"]]
                else:
                    await interaction.response.send_message(f"{interaction.user.mention} No previous song found.", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                    return
                # Stop the current song
                voice_client.stop() # This will trigger the after callback to play the next song in the queue

                # Inform the user that the song was skipped
                await interaction.response.send_message(f"{interaction.user.mention} Playing previous song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                previous_url = queues[guild_id]["played"].pop(-1) if queues[guild_id]["played"] else None
                if previous_url:
                    queues[guild_id]["queue"] = [previous_url, *queues[guild_id]["queue"]]
                    voice_client.stop() # This will trigger the after callback to play the next song in the queue
                    await interaction.response.send_message(f"{interaction.user.mention} Playing previous song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await interaction.response.send_message(f"{interaction.user.mention} No previous song found.", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        
        except Exception as e:
            logger.error(f"Error skipping the song: {e}")
            await interaction.response.send_message(f"```ansi\n[2;31mI'm unable to skip the song at the moment```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())

    async def pause_resume_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "pause/resume"})
        try:
            voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if voice_client:
                if voice_client.is_paused():
                    voice_client.resume()
                    await interaction.response.send_message(f"{interaction.user.mention} Resumed the song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    voice_client.pause()
                    await interaction.response.send_message(f"{interaction.user.mention} Paused the song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                await interaction.response.send_message(f"{interaction.user.mention} Im not currently playing anything!", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            logger.error(f"Error pausing/resuming the song: {e}")
            await interaction.response.send_message(f"```ansi\n[2;31mI'm unable to pause or resume the song at the moment```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())

    async def skip_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "skip"})
        guild_id = interaction.guild.id
    
        # Get the voice client for the guild
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        try:
            if voice_client and voice_client.is_playing():
                # Stop the current song
                voice_client.stop() # This will trigger the after callback to play the next song in the queue

                await interaction.response.send_message(f"{interaction.user.mention} Skipped the song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                if queues[guild_id]["queue"] and not voice_client.is_playing():
                    await self.play_next(interaction)
                    await interaction.response.send_message(f"{interaction.user.mention} Skipped the song.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await interaction.response.send_message(f"{interaction.user.mention} No song is currently playing, or other items in the queue", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        except ValueError as e:
            logger.error(f"Error skipping the song: {e}")
            await interaction.response.send_message(f"```ansi\n[2;31mI'm unable to skip the song at the moment```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
    
    async def queue_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "queue"})
        self.queue_modal = BaseModal(title="Enter the youtube URL")
        
        self.queue_modal.add_item(discord.ui.TextInput(label="URL", placeholder="Enter the YouTube URL of the Song or Playlist", min_length=15, max_length=100))
        self.queue_modal.on_submit = self.queue_modal_callback
        await interaction.response.send_modal(self.queue_modal)
        
    async def queue_modal_callback(self, interaction: discord.Interaction) -> None:
        url = typing.cast(discord.ui.TextInput[BaseModal], self.queue_modal.children[0]).value
        logger.command(interaction, {"command": "queue_modal_callback", "url": url})
        guild_id = interaction.guild.id

        # Specify the channel ID or name you want the bot to join
        # You can use the channel ID directly for accuracy, or fetch it by name
        music_channel = discord.utils.get(interaction.guild.voice_channels, id=ids[guild_id]["music_voice_id"])

        if music_channel is None:
            await interaction.response.send_message("```ansi\n[2;31mThe specified voice channel does not exist. please update the channel ID.```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            return
        
        # Get video or playlist URLs
        video_urls = get_video_urls(url)
        if video_urls == []:
            await interaction.response.send_message("```ansi\n[2;31mInvalid URL or no video(s) were found.```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            return
        if video_urls == "radio":
            await interaction.response.send_message("```ansi\n[2;31mThis is a radio URL and cannot be processed.", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            return
        
        if self.client.voice_clients and guild_id in voice_clients:
            voice_client = voice_clients[guild_id]
        else:
            try:
                # Connect to the specific voice channel
                voice_client = await music_channel.connect()
                voice_clients[guild_id] = voice_client
            except TypeError as e:
                logger.error(f"Error connecting to the voice channel: {e}")
                await interaction.response.send_message("```ansi\n[2;31mAn error occurred while trying to connect to the voice channel.```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                return

        # If there's no queue for this guild, create one
        if guild_id not in queues:
            queues[guild_id] = {"played":[], "current": {}, "queue":[]}

        # If the bot is not already playing music, play the first song in the queue
        if not voice_clients[guild_id].is_playing():
            # Add video URLs to the queue
            queues[guild_id]["queue"] = [*queues[guild_id]["queue"], *video_urls]
            if len(video_urls) > 1:
                await interaction.response.send_message(f"{interaction.user.mention} Playing the queue and added {len(video_urls)-1} song(s) to the queue.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                await interaction.response.send_message(f"{interaction.user.mention} Playing the song", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            await self.play_next(interaction)
        else:
            # Add video URLs to the queue
            queues[guild_id]["queue"] = [*queues[guild_id]["queue"], *video_urls]
            await interaction.response.send_message(f"{interaction.user.mention} Added {len(video_urls)} song(s) to the queue.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
    
    async def clear_queue_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "clear_queue"})
        guild_id = interaction.guild_id
        if guild_id in queues:
            queues.pop(guild_id)
            await interaction.response.send_message(f"{interaction.user.mention} Queue and history cleared!", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message(f"{interaction.user.mention} There is no queue or history to clear", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
    
    async def stop_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction, {"command": "stop"})
        try:
            guild_id = interaction.guild_id
            if guild_id in voice_clients:
                voice_client = voice_clients[guild_id]
                queues.pop(guild_id)
                voice_client.stop()
                await voice_client.disconnect()
                voice_clients.pop(guild_id)
                await interaction.response.send_message(f"{interaction.user.mention} Stopped the song and disconnected.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                await interaction.response.send_message(f"{interaction.user.mention} Im not currently connected", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        except KeyError as e:
            guild_id = interaction.guild_id
            if guild_id in voice_clients:
                voice_client = voice_clients[guild_id]
                voice_client.stop()
                await voice_client.disconnect()
                voice_clients.pop(guild_id)
                await interaction.response.send_message(f"{interaction.user.mention} Stopped the song and disconnected.", delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            logger.error(f"Error stopping the song: {e}")
            await interaction.response.send_message(f"```ansi\n[2;31mI'm unable to stop the song at the moment```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
    
    async def loop_callback(self, interaction: discord.Interaction) -> None:
        pass
    
    async def shuffle_callback(self, interaction: discord.Interaction) -> None:
        pass
    
    async def volume_mute_callback(self, interaction: discord.Interaction) -> None:
        pass
    
    async def volume_up_callback(self, interaction: discord.Interaction) -> None:
        pass
    
    async def volume_down_callback(self, interaction: discord.Interaction) -> None:
        pass
    
    # player functions for music
    async def play_next(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id
        music_spam_channel = self.client.get_channel(ids[guild_id]["music_channel_id"])
        # Check if there are songs in the queue
        if guild_id in queues and queues[guild_id]["queue"]:
            next_url = queues[guild_id]["queue"].pop(0)  # Get the next song from the queue
            previous_url = queues[guild_id]["current"]["original_url"] if queues[guild_id]["current"] else None
            if previous_url:
                queues[guild_id]["played"].append(previous_url)  # Add the song to the played list
            loop = asyncio.get_event_loop()

            try:
                # Extract song info
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(next_url, download=False))
                queues[guild_id]["current"] = data  # Set the current song to the next song
                logger.debug(f"Playing: {queues[guild_id]['current']['title']}\ncurrent first 10 queue items: {queues[guild_id]['queue'][0:10]}\nplayed: {queues[guild_id]['played']}")
                song_url = data['url']
                
                player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

                # Play the song and set the after callback to play the next song in the queue
                if not voice_clients[guild_id].is_connected():
                    music_channel = discord.utils.get(interaction.guild.voice_channels, id=ids[guild_id]["music_voice_id"])

                    if music_channel is None:
                        await interaction.response.send_message("```ansi\n[2;31mThe specified voice channel does not exist. please update the channel ID.```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                        return
                    try:
                        # Connect to the specific voice channel
                        voice_client: discord.VoiceClient = await music_channel.connect()
                        voice_clients[guild_id] = voice_client
                    except TypeError as e:
                        logger.error(f"Error connecting to the voice channel: {e}")
                        await interaction.response.send_message("```ansi\n[2;31mAn error occurred while trying to connect to the voice channel.```", ephemeral=True, delete_after=20, silent=True, allowed_mentions=discord.AllowedMentions.none())
                        return
                try:
                    voice_clients[guild_id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction), self.client.loop))
                except discord.errors.ClientException:
                    pass
                await music_spam_channel.send(f"Now playing: **{data['title']}**", delete_after=20*60) # Delete after 20 minutes to keep channel a bit clean
            except yt_dlp.DownloadError as e:
                logger.error(f"Error downloading the song: {e}")
                await music_spam_channel.send(f"```ansi\n[2;31mAn error occurred while trying to download the song. Skipping to the next song.```", delete_after=10)
                # voice_client.stop()
                await self.play_next(interaction)  # Automatically attempt to play the next song
            except Exception as e:
                logger.error(f"Error playing the song: {e}")
                await music_spam_channel.send(f"```ansi\n[2;31mAn error occurred while trying to play the song. Skipping to the next song.```", delete_after=10)

                # If an error occurs, skip to the next song
                await self.play_next(interaction)  # Automatically attempt to play the next song
        else:
            # No more songs in the queue
            await music_spam_channel.send("The queue is empty, no more songs to play.", delete_after=10)