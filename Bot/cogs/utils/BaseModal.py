import traceback
import discord

from logger import logger

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
        message = f"An error occurred while processing the URL, Please check the URL and try again."
        logger.error(f"An error occurred while processing the URL, Please check the URL and try again.{tb}, {error}")
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except discord.InteractionResponded:
            logger.error("An error occurred while processing the URL, Please check the URL and try again.")
        #     await interaction.edit_original_response(content=message, view=PersistentMusicView())
        self.stop()

    @property
    def interaction(self) -> discord.Interaction | None:
        return self._interaction