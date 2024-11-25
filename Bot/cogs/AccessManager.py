import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select

from functions import load_ids, create_connection, close_connection, get_accepted_rules, get_rule_channels, create_rule_channel, remove_rule_channel, set_accepted_rules, get_rule_channel

# local imports
from logger import logger

ids = load_ids()

class AccessManager(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
    
    # Check if the user is a runner or Tech Oracle or above
    def is_eventlumi() -> bool:
        async def predicate(interaction: discord.Interaction) -> bool:
            allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
            if any(role.id in allowed_roles for role in interaction.user.roles):
                logger.debug("User has the required role to use this command.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                return True
            logger.info("User does not have the required role to use this command.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.response.send_message("You do not have the required role to use this command.", ephemeral=True)
            return False
        return app_commands.check(predicate)
    
    @app_commands.command(name="createrulegate", description="Creates an access barier for a channel, so that someone must accept the rules to access the channel.")
    @is_eventlumi()
    async def createRuleGate(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        if channel.type == discord.ChannelType.voice:
            logger.warning("The channel can't be a voice channel.")
            await interaction.followup.send(content="The channel can't be a voice channel.", ephemeral=True)
            return
        
        event_luminary_role = interaction.guild.get_role(ids[interaction.guild.id]["event_luminary_role_id"])
        if not event_luminary_role:
            logger.critical("Event Luminary role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mEvent Luminary role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        sky_guardians_role = interaction.guild.get_role(ids[interaction.guild.id]["sky_guardians_role_id"])
        if not sky_guardians_role:
            logger.critical("Sky Guardians role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mSky Guardians role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        tech_oracle_role = interaction.guild.get_role(ids[interaction.guild.id]["tech_oracle_role_id"])
        if not tech_oracle_role:
            logger.critical("Tech Oracle role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mTech Oracle role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        current_channel = interaction.channel
        
        connection = create_connection("Server_data")
        if get_rule_channel(connection, channel.id):
            close_connection(connection)
            logger.warning("The channel already has a rule gate set.")
            await interaction.followup.send("The channel already has a rule gate set.", ephemeral=True)
            return
        create_rule_channel(connection, channel.id, interaction.user.id)
        close_connection(connection)
        
        # Set the permissions for the channel allow only the read_messages permission for the default role
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, add_reactions=False, send_messages=False),
            event_luminary_role: discord.PermissionOverwrite(read_messages=True, add_reactions=True, send_messages=True, manage_messages=True, manage_channels=True, manage_thread=True),
            sky_guardians_role: discord.PermissionOverwrite(read_messages=True, add_reactions=True, send_messages=True, manage_messages=True, manage_channels=True, manage_thread=True),
            tech_oracle_role: discord.PermissionOverwrite(read_messages=True, add_reactions=True, send_messages=True, read_message_history=True, manage_messages=True, manage_channels=True, manage_permissions=True, administrator=True),
        }
        
        channel = await channel.edit(overwrites=overwrites)
        
        logger.info("The rules have been added to the channel.", {"channel_id": channel.id, "channel_name": channel.name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name})
        
        await interaction.followup.send("The rules have been added to the channel.", ephemeral=True)
        await current_channel.send("", view=PersistentAcceptRulesView(self.client, channel))

    @app_commands.command(name="removerulegate", description="Removes a channels post and reaction access barier.")
    @is_eventlumi()
    async def removeRuleGate(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        if channel.type == discord.ChannelType.voice:
            logger.warning("The channel can't be a voice channel.")
            await interaction.followup.send(content="The channel can't be a voice channel.", ephemeral=True)
            return
        
        event_luminary_role = interaction.guild.get_role(ids[interaction.guild.id]["event_luminary_role_id"])
        if not event_luminary_role:
            logger.critical("Event Luminary role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mEvent Luminary role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        sky_guardians_role = interaction.guild.get_role(ids[interaction.guild.id]["sky_guardians_role_id"])
        if not sky_guardians_role:
            logger.critical("Sky Guardians role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mSky Guardians role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        tech_oracle_role = interaction.guild.get_role(ids[interaction.guild.id]["tech_oracle_role_id"])
        if not tech_oracle_role:
            logger.critical("Tech Oracle role not found. Please provide a valid role ID.")
            await interaction.followup.send("```ansi\n[2;31mTech Oracle role not found. Please provide a valid role ID.```", ephemeral=True)
            return
        
        connection = create_connection("Server_data")
        if not get_rule_channel(connection, channel.id):
            close_connection(connection)
            logger.warning("The channel does not have a rule gate set.")
            await interaction.followup.send("The channel does not have a rule gate set.", ephemeral=True)
            return
        remove_rule_channel(connection, channel.id)
        close_connection(connection)
        
        # Set the permissions for the channel allow only the read_messages permission for the default role
        overwrites = {
            event_luminary_role: discord.PermissionOverwrite(read_messages=True, add_reactions=True, send_messages=True, manage_messages=True, manage_channels=True, manage_thread=True),
            tech_oracle_role: discord.PermissionOverwrite(read_messages=True, add_reactions=True, send_messages=True, read_message_history=True, manage_messages=True, manage_channels=True, manage_permissions=True, administrator=True),
        }
        
        channel = await channel.edit(overwrites=overwrites)
        
        logger.info("The rules have been removed from the channel.", {"channel_id": channel.id, "channel_name": channel.name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name})
        
        await interaction.followup.send("The rules have been removed from the channel.", ephemeral=True)


class PersistentAcceptRulesView(discord.ui.View):
    def __init__(self, client: commands.Bot, channel: discord.abc.GuildChannel) -> None:
        super().__init__(timeout=None)  
        self.add_item(discord.ui.Button(label="📜 I have read the rules", style=discord.ButtonStyle.blurple, custom_id=f"Accepted_rules_{channel.id}"))
        self.children[-1].callback = self.accept_callback
        self.client = client
        self.channel = channel

    async def accept_callback(self, interaction: discord.Interaction) -> None:
        logger.command(interaction)
        await interaction.response.defer()
        
        if not self.channel:
            logger.warning("Channel not found.")
            return
        
        connection = create_connection("Server_data")
        if not get_rule_channel(connection, self.channel.id):
            close_connection(connection)
            logger.warning("The channel does not have a rule gate set.")
            await interaction.followup.send("The channel does not have a rule gate set.", ephemeral=True)
            return
        close_connection(connection)
        
        ignore_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["event_luminary_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
        if any(role.id in ignore_roles for role in interaction.user.roles):
            logger.debug("User has the required role to use this command.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send("You have already have full access to this channel", ephemeral=True)
            return
        
        connection = create_connection("Server_data")
        accepted_users = get_accepted_rules(connection, self.channel.id)
        if not accepted_users:
            accepted_users = []
        for user in accepted_users:
            if user["user_id"] == interaction.user.id:
                logger.info("User has already accepted the rules.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send("You have already accepted the rules.", ephemeral=True)
                return
    
        logger.info("User has accepted the rules.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel })
        
        set_accepted_rules(connection, self.channel.id, interaction.user.id)
        close_connection(connection)
        overwite = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        await self.channel.set_permissions(interaction.user, overwrite=overwite)
        
        logger.success("You have accepted the rules!", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel})

        await interaction.followup.send("You have accepted the rules!\nYou can now post your submition!", ephemeral=True)