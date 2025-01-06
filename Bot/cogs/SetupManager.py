import typing
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select

from functions import load_ids, create_connection, close_connection, get_accepted_rules, get_rule_channels, create_rule_channel, remove_rule_channel, set_accepted_rules, get_rule_channel

# local imports
from logger import logger
from cogs.utils.BaseView import BaseView

ids = load_ids()


class SetupManager(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
    
    # Check if the user is a runner or Tech Oracle or above
    def is_owner() -> bool:
        async def predicate(interaction: discord.Interaction) -> bool:
            guild = interaction.guild
            if not guild:
                logger.warning("The guild was not found.")
                return False
            serverOwner: discord.Member = guild.owner
            if interaction.user.id == serverOwner.id:
                logger.debug("User is the server owner.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                return True
            logger.info("User is not the server owner.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.response.send_message("You must be the server owner to use this command", ephemeral=True)
            return False
        return app_commands.check(predicate)
    
    @app_commands.command(name="setup_roles", description="Set the bot up with the server roles or create them if they don't exist.")
    @is_owner()
    async def setupRoles(self, interaction: discord.Interaction, ownerRole: discord.Role, moderatorRole: discord.Role, techRole: discord.Role, eventOrganiserRole: discord.Role, memberRole: discord.Role) -> None:
        logger.command(interaction)
        guild = interaction.guild
        if not guild:
            logger.warning("The guild was not found.")
            return
        
        logger.debug("Setting up the server roles...", {"guild_id": guild.id, "guild_name": guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM roles WHERE guild_id = {guild.id}")
        result = cursor.fetchone()
        if result:
            cursor.execute(f"UPDATE roles SET owner_role_id = {ownerRole.id}, moderator_role_id = {moderatorRole.id}, tech_role_id = {techRole.id}, event_organiser_role_id = {eventOrganiserRole.id}, member_role_id = {memberRole.id} WHERE guild_id = {guild.id}")
        else:
            cursor.execute(f"INSERT INTO roles (guild_id, owner_role_id, moderator_role_id, tech_role_id, event_organiser_role_id, member_role_id) VALUES ({guild.id}, {ownerRole.id}, {moderatorRole.id}, {techRole.id}, {eventOrganiserRole.id}, {memberRole.id})")
        connection.commit()
        close_connection(connection)
        await interaction.response.send_message("Server roles have been set up.", ephemeral=True) 
        
    
    # @app_commands.command(name="setup_server", description="Set up the server with the specific roles and channels.")
    # @is_owner()
    # async def setupServer(self, interaction: discord.Interaction) -> None:
    #     # we cant defer the response here as we need to send a modal
    #     logger.command(interaction)
    #     guild = interaction.guild
    #     if not guild:
    #         logger.warning("The guild was not found.")
    #         return
        
    #     channel = interaction.channel
        
        # view = RoleMenu(interaction.user) # create the view with the user who invoked the command
        # await interaction.response.send_message("Chose the roles for the server", view=view)
        # await channel.send("Choose the Owner Role", view=view)
        # await channel.send("Choose the Moderator Role", view=view)
        # await channel.send("Choose the Tech Role", view=view)
        # await channel.send("Choose the Event Organiser Role", view=view)
        # await channel.send("Choose the Member Role", view=view)
        # await interaction.followup.send("Setting up the server...", ephemeral=True)


# class RoleMenu(BaseView):
#     def __init__(self, user: discord.User) -> None:
#         super().__init__(user=user, allow_others=False)
#         self.add_item(discord.ui.RoleSelect(placeholder="Select the Owner Role", min_values=1, max_values=1))
#         self.children[-1].callback = None
#         self.add_item(discord.ui.RoleSelect(placeholder="Select the Moderator Role", min_values=1, max_values=1))
#         self.children[-1].callback = None
#         self.add_item(discord.ui.RoleSelect(placeholder="Select the Tech Role", min_values=1, max_values=1))
#         self.children[-1].callback = None
#         self.add_item(discord.ui.RoleSelect(placeholder="Select the Event Organiser Role", min_values=1, max_values=1))
#         self.children[-1].callback = None
#         self.add_item(discord.ui.RoleSelect(placeholder="Select the Member Role", min_values=1, max_values=1))
#         self.children[-1].callback = None
#         # self.add_item(discord.ui.Button(label="Finish", style=discord.ButtonStyle.green))
#         # self.children[-1].callback = self.finish_callback
#         # self
        
#     async def finish_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect) -> None:
#         await interaction.response.defer()
#         await interaction.followup.send(f"You selected {select.values[0]}\n {select.values[1]}, {select.values[2]}, {select.values[3]}, {select.values[4]}", ephemeral=True)