from __future__ import annotations

# discord imports
import discord
from discord.ext import commands

# python imports
import typing
import asyncio
import traceback

# local imports
from functions import load_ids, get_video_urls

# 3rd party imports
import yt_dlp

voice_clients: dict[int, discord.VoiceChannel] = {}
queues: dict = {}

ids = load_ids()

# music settings
yt_dlp_options: dict[str, str] = {"format": "bestaudio/best", 'noplaylist': False, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
ffmpeg_options: dict[str, str] = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

# youtube variables
youtube_base_url: str = 'https://www.youtube.com/'
youtube_results_url: str = youtube_base_url + 'results?'
youtube_watch_url: str = youtube_base_url + 'watch?v='
ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(yt_dlp_options)


class BaseModal(discord.ui.Modal):
    _interaction: discord.Interaction | None = None

    # sets the interaction attribute when a valid interaction is received i.e modal is submitted
    # via this we can know if the modal was submitted or it timed out
    async def on_submit(self, interaction: discord.Interaction) -> None:
        # if not responded to, defer the interaction
        if not interaction.response.is_done():
            await interaction.response.defer()
        self._interaction = interaction
        self.stop()

    # make sure any errors don't get ignored
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        message = f"An error occurred while processing the interaction:\n```py\n{tb}\n```"
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_response(content=message, view=None)
        self.stop()

    @property
    def interaction(self) -> discord.Interaction | None:
        return self._interaction


class PersistentMusicView(discord.ui.View):
    def __init__(self, client: commands.Bot):
        super().__init__(timeout=None)  
        self.add_item(discord.ui.Button(emoji="<:Pause:1284205904933158952>", style=discord.ButtonStyle.primary, custom_id="pause", row=1))
        self.children[-1].callback = self.pause_callback
        self.add_item(discord.ui.Button(emoji="<:Play:1284205906820595865>", style=discord.ButtonStyle.primary, custom_id="resume", row=1))
        self.children[-1].callback = self.resume_callback
        self.add_item(discord.ui.Button(emoji="<:Skip:1284205910365044847>", style=discord.ButtonStyle.success, custom_id="skip", row=1))
        self.children[-1].callback = self.skip_callback
        self.add_item(discord.ui.Button(emoji="<:Queue:1284205908473417789>", style=discord.ButtonStyle.secondary, custom_id="queue", row=2))
        self.children[-1].callback = self.queue_callback
        self.add_item(discord.ui.Button(emoji="<:Clear_Queue:1284205901791887524>", style=discord.ButtonStyle.secondary, custom_id="clear_queue", row=2))
        self.children[-1].callback = self.clear_queue_callback
        self.add_item(discord.ui.Button(emoji="<:Close:1284205903343648870>", style=discord.ButtonStyle.danger, custom_id="stop", row=2))
        self.children[-1].callback = self.stop_callback
        self.client = client
    
    async def pause_callback(self, interaction: discord.Interaction) -> None:
        try:
            voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if voice_client and voice_client.is_playing():
                voice_client.pause()
                await interaction.response.send_message("Paused the song.", delete_after=10)
            else:
                await interaction.response.send_message("No song is currently playing.", ephemeral=True)
        except Exception as e:
            print(f"[error][player] Error pausing the song: {e}")
            await interaction.response.send_message(f"```fix\nI'm unable to pause the song at the moment```", ephemeral=True)
    
    async def resume_callback(self, interaction: discord.Interaction) -> None:
        try:
            voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if voice_client and voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message("Resumed the song.", delete_after=10)
            else:
                await interaction.response.send_message("No song is currently paused.", ephemeral=True)
        except Exception as e:
            print(f"[error][player] Error resuming the song: {e}")
            await interaction.response.send_message(f"```fix\nI'm unable to resume the song at the moment```", ephemeral=True)

    async def skip_callback(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id
    
        # Get the voice client for the guild
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        try:
            if voice_client and voice_client.is_playing():
                # Stop the current song
                voice_client.stop()

                # Inform the user that the song was skipped
                await interaction.response.send_message("Skipped the song.", delete_after=10)
            else:
                await interaction.response.send_message("No song is currently playing.", ephemeral=True)
        except Exception as e:
            print(f"[error][player] Error skipping the song: {e}")
            await interaction.response.send_message(f"```fix\nI'm unable to skip the song at the moment```", ephemeral=True)
    
    async def queue_callback(self, interaction: discord.Interaction) -> None:
        self.queue_modal = BaseModal(title="Enter the youtube URL")
        
        self.queue_modal.add_item(discord.ui.TextInput(label="URL", placeholder="Enter the YouTube URL of the Song or Playlist", min_length=15, max_length=100))
        self.queue_modal.on_submit = self.queue_modal_callback
        await interaction.response.send_modal(self.queue_modal)
        
    async def queue_modal_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()  # Defer to allow time for processing
        url = typing.cast(discord.ui.TextInput[BaseModal], self.queue_modal.children[0]).value

        guild_id = interaction.guild.id

        # Specify the channel ID or name you want the bot to join
        # You can use the channel ID directly for accuracy, or fetch it by name
        music_channel = discord.utils.get(interaction.guild.voice_channels, id=ids[guild_id]["music_voice_id"])

        if music_channel is None:
            await interaction.followup.send("```fix\nThe specified voice channel does not exist. please update the channel ID.```", ephemeral=True)
            return
        
        if self.client.voice_clients and guild_id in voice_clients:
            voice_client = voice_clients[guild_id]
        else:
            try:
                # Connect to the specific voice channel
                voice_client = await music_channel.connect()
                voice_clients[guild_id] = voice_client
            except TypeError as e:
                print(f"[error][player] Error connecting to the voice channel: {e}")
                await interaction.followup.send("```fix\nAn error occurred while trying to connect to the voice channel.```", ephemeral=True)
                return

        # Get video or playlist URLs
        video_urls = get_video_urls(url)
        if video_urls == []:
            await interaction.followup.send("```fix\nInvalid URL or no video(s) were found.```", ephemeral=True)
            return
        if video_urls == "radio":
            await interaction.followup.send("```fix\nThis is a radio URL and cannot be processed.", ephemeral=True)
            return

        # If there's no queue for this guild, create one
        if guild_id not in queues:
            queues[guild_id] = []

        # If the bot is not already playing music, play the first song in the queue
        if not voice_clients[guild_id].is_playing():
            # Add video URLs to the queue
            queues[guild_id].extend(video_urls)
            if len(video_urls) > 1:
                await interaction.followup.send(f"Added {len(video_urls)-1} to the queue.", ephemeral=True)
            await interaction.followup.send("Now playing in the music channel.", ephemeral=True)
            await self.play_next(interaction)
        else:
            # Add video URLs infront of the queue
            queues[guild_id] = [*queues[guild_id], *video_urls]
            await interaction.followup.send(f"Added {len(video_urls)} to the queue.", ephemeral=True)
    
    async def clear_queue_callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild.id in queues:
            queues[interaction.guild.id].clear()
            await interaction.response.send_message("Queue cleared!", delete_after=10)
        else:
            await interaction.response.send_message("There is no queue to clear", ephemeral=True)
    
    async def stop_callback(self, interaction: discord.Interaction) -> None:
        try:
            guild_id = interaction.guild_id
            voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if voice_client:
                queues[guild_id] = []  # Clear the queue
                voice_client.stop()
                await voice_client.disconnect()
                await interaction.response.send_message("Stopped the song and disconnected.", delete_after=10)
            else:
                await interaction.response.send_message("No song is currently playing.", ephemeral=True)
        except Exception as e:
            print(f"[error][player] Error stopping the song: {e}")
            await interaction.response.send_message(f"```fix\nI'm unable to stop the song at the moment```", ephemeral=True)
    
    # player functions for music
    async def play_next(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id
        music_spam_channel = self.client.get_channel(ids[guild_id]["music_channel_id"])
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
                voice_clients[guild_id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction), self.client.loop))

                await music_spam_channel.send(f"Now playing: **{data['title']}**", delete_after=10*60) # Delete after 10 minutes to keep channel a bit clean
            except yt_dlp.DownloadError as e:
                print(f"[error][play_next] Error downloading the song: {e}")
                await music_spam_channel.send(f"```fix\nAn error occurred while trying to download the song. Skipping to the next song.```", delete_after=10)
                await self.play_next(interaction)  # Automatically attempt to play the next song
            except Exception as e:
                print(f"[error][play_next] Error playing the song: {e}")
                await music_spam_channel.send(f"```fix\nAn error occurred while trying to play the song. Skipping to the next song.```", delete_after=10)

                # If an error occurs, skip to the next song
                await self.play_next(interaction)  # Automatically attempt to play the next song
        else:
            # No more songs in the queue
            await music_spam_channel.send("The queue is empty, no more songs to play.", delete_after=10)
