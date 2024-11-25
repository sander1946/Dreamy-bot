import discord
from discord import app_commands
from discord.ext import commands

from functions import load_ids

# local imports
from logger import logger

ids = load_ids()

teams: dict[str, dict] = {}  # Dictionary to store the team data

class RunManager(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
    
    # Check if the user is a runner or Tech Oracle or above
    def is_runner() -> bool:
        async def predicate(interaction: discord.Interaction) -> bool:
            allowed_roles: list[int] = [ids[interaction.guild.id]["sancturary_keeper_role_id"], ids[interaction.guild.id]["sky_guardians_role_id"], ids[interaction.guild.id]["tech_oracle_role_id"]]
            if interaction.user.id in [152948524458180609, 496387339388452864, 787737643630329896] or any(role.id in allowed_roles for role in interaction.user.roles): # Allow tech oracles and up to use the command and Odd and Eli
                logger.debug(f"User {interaction.user.display_name} is allowed to use the command.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                return True
            logger.debug(f"User {interaction.user.display_name} is not allowed to use the command.", {"user_id": interaction.user.id, "username": interaction.user.name, "display_name": interaction.user.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.response.send_message("You do not have the required role to use this command.", ephemeral=True)
            return False
        return app_commands.check(predicate)
    
    # Run commands
    @app_commands.command(name="createrun", description="Create a team with a leader and an emoji.")
    @is_runner()
    async def createrun(self, interaction: discord.Interaction, guide: discord.Member = None, member1: discord.Member = None, member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None, member5: discord.Member = None, member6: discord.Member = None, member7: discord.Member = None) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        
        if guide is None:
            guide = interaction.user
        
        if interaction.guild.id not in teams:
            teams[interaction.guild.id] = {}
        
        if guide.id in teams[interaction.guild.id]:
            logger.debug(f"{guide.display_name} already leads a run.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} already leads a run.", ephemeral=True)
            return
        
        logger.info(f"Creating a run with {guide.display_name}:{guide.id} as the runner.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Update the team message
        members = []
        member_mentions = []
        for member in [member1, member2, member3, member4, member5, member6, member7]:
            if member is None:
                continue
            if member.id == guide.id:
                logger.debug(f"User {member.display_name} tried to add themselves to the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send("You cannot add yourself to the run.", ephemeral=True)
                continue
            if member in members:
                logger.debug(f"User {member.display_name} is already in the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send(f"{member.name} is already in the run.", ephemeral=True)
                continue
            members.append(member)
            member_mentions.append(member.mention)
        logger.debug(f"Members in the run: {member_mentions}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        member_names_str = "\n".join(member_mentions)
        
        await interaction.followup.send(f"The Run leady by {guide.display_name} has been created!", ephemeral=True)
        team_message = f"__**Run Guide**__\n{guide.mention}\n\n__**Runners**__\n{member_names_str}\n-# {len(members)+1}/8"

        message = await interaction.channel.send(team_message, silent=True, allowed_mentions=discord.AllowedMentions.none())
        logger.debug(f"Team message sent: {team_message}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        # Save team information
        teams[interaction.guild.id][guide.id] = {
            "message_id": message.id,
            "members": members,
            "channel_id": interaction.channel.id,  # Track the channel ID
        }
        
    @app_commands.command(name="addrunners", description="Create a team with a leader and an emoji.")
    @is_runner()
    async def addrunners(self, interaction: discord.Interaction, guide: discord.Member = None, member1: discord.Member = None, member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None, member5: discord.Member = None, member6: discord.Member = None, member7: discord.Member = None) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        
        if guide is None:
            guide = interaction.user
            
        if interaction.guild.id not in teams:
            teams[interaction.guild.id] = {}
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
            
        if guide.id not in teams[interaction.guild.id]:
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
        
        logger.debug(f"Updating the run with {guide.display_name}:{guide.id} as the runner.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Update the team message
        members = teams[interaction.guild.id][guide.id]["members"]
        member_mentions = []
        
        for member in members:
            member_mentions.append(member.mention)

        for member in [member1, member2, member3, member4, member5, member6, member7]:
            if member is None:
                continue
            if member.id == guide.id:
                logger.debug(f"User {member.display_name} tried to add themselves to the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send("You cannot add yourself to the run.", ephemeral=True)
                continue
            if member in members:
                logger.debug(f"User {member.display_name} is already in the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send(f"{member.name} is already in the run.", ephemeral=True)
                continue
            members.append(member)
            member_mentions.append(member.mention)
        
        logger.debug(f"Members in the run: {member_mentions}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        member_names_str = "\n".join(member_mentions)
        
        team_message = f"__**Run Guide**__\n{guide.mention}\n\n__**Runners**__\n{member_names_str}\n-# {len(members)+1}/8"
        
        # delete the old message
        message_id = teams[interaction.guild.id][guide.id]["message_id"]
        channel_id = teams[interaction.guild.id][guide.id]["channel_id"]
        
        # Delete the team message
        channel = self.client.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound:
            logger.error(f"Message not found: {message_id}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})

        # Send the new message
        message = await interaction.channel.send(team_message, silent=True, allowed_mentions=discord.AllowedMentions.none())
        
        logger.debug(f"Team message sent: {team_message}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Save team information
        teams[interaction.guild.id][guide.id] = {
            "message_id": message.id,
            "members": members,
            "channel_id": interaction.channel.id,  # Track the channel ID
        }

    @app_commands.command(name="removerunners", description="Create a team with a leader and an emoji.")
    @is_runner()
    async def removerunners(self, interaction: discord.Interaction, guide: discord.Member = None, member1: discord.Member = None, member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None, member5: discord.Member = None, member6: discord.Member = None, member7: discord.Member = None) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        
        if guide is None:
            guide = interaction.user
            
        if interaction.guild.id not in teams:
            teams[interaction.guild.id] = {}
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name}) 
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
            
        if guide.id not in teams[interaction.guild.id]:
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
        
        logger.debug(f"Updating the run with {guide.display_name}:{guide.id} as the runner.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Update the team message
        members = teams[interaction.guild.id][guide.id]["members"]
        member_mentions = []
        
        for member in [member1, member2, member3, member4, member5, member6, member7]:
            if member is None:
                continue
            if member.id == guide.id:
                logger.debug(f"User {member.display_name} tried to remove themselves from the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send("You cannot remove yourself from the run.", ephemeral=True)
                continue
            if member not in members:
                logger.debug(f"User {member.display_name} is not in the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send(f"{member.display_name} is not in the run.", ephemeral=True)
                continue
            members.remove(member)
        
        for member in members:
            member_mentions.append(member.mention)
        
        logger.debug(f"Members in the run: {member_mentions}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        member_names_str = "\n".join(member_mentions)
        
        team_message = f"__**Run Guide**__\n{guide.mention}\n\n__**Runners**__\n{member_names_str}\n-# {len(members)+1}/8"
        
        # delete the old message
        message_id = teams[interaction.guild.id][guide.id]["message_id"]
        channel_id = teams[interaction.guild.id][guide.id]["channel_id"]
        
        # Delete the team message
        channel = self.client.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound:
            logger.error(f"Message not found: {message_id}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})

        # Send the new message
        message = await interaction.channel.send(team_message, silent=True, allowed_mentions=discord.AllowedMentions.none())

        logger.debug(f"Team message sent: {team_message}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Save team information
        teams[interaction.guild.id][guide.id] = {
            "message_id": message.id,
            "members": members,
            "channel_id": interaction.channel.id,  # Track the channel ID
        }
    
    @app_commands.command(name="splitrun", description="Create a team with a leader and an emoji.")
    @is_runner()
    async def splitrun(self, interaction: discord.Interaction, new_guide: discord.Member, current_guide: discord.Member = None, member1: discord.Member = None, member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None, member5: discord.Member = None, member6: discord.Member = None, member7: discord.Member = None) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        
        if current_guide is None:
            current_guide = interaction.user
        
        if interaction.guild.id not in teams:
            teams[interaction.guild.id] = {}
            logger.debug(f"{current_guide.display_name} does not lead a run at the moment.", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{current_guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
        
        if current_guide.id not in teams[interaction.guild.id]:
            logger.debug(f"{current_guide.display_name} does not lead a run at the moment.", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{current_guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
        
        if new_guide.id in teams[interaction.guild.id]:
            logger.debug(f"{new_guide.display_name} already leads a run.", {"user_id": new_guide.id, "username": new_guide.name, "display_name": new_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{new_guide.display_name} already leads a run.", ephemeral=True)
            return
        
        logger.debug(f"Splitting the run with {current_guide.display_name}:{current_guide.id} as the runner.", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        # Update the team message
        current_members = teams[interaction.guild.id][current_guide.id]["members"]
        current_members_mentions = []
        new_guide_members = []
        new_guide_member_mentions = []
        
        if new_guide in current_members:
            current_members.remove(new_guide)
        
        for member in [member1, member2, member3, member4, member5, member6, member7]:
            if member is None:
                continue
            if member.id == current_guide.id:
                logger.debug(f"User {member.display_name} tried to add themselves to the run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send("You cannot remove yourself from the run.", ephemeral=True)
                continue
            if member not in current_members:
                logger.debug(f"User {member.display_name} is not in the run, adding them to the new run.", {"user_id": member.id, "username": member.name, "display_name": member.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
                await interaction.followup.send(f"{member.display_name} is not in the run, adding them to the new run.", ephemeral=True)
                new_guide_members.append(member)
                continue
            current_members.remove(member)
            new_guide_members.append(member)
        
        for member in current_members:
            current_members_mentions.append(member.mention)
        
        for member in new_guide_members:
            new_guide_member_mentions.append(member.mention)
        
        logger.debug(f"Members in the current run: {current_members_mentions}", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        current_member_names_str = "\n".join(current_members_mentions)
        new_guide_member_names_str = "\n".join(new_guide_member_mentions)
        
        current_team_message = f"__**Run Guide**__\n{current_guide.mention}\n\n__**Runners**__\n{current_member_names_str}\n-# {len(current_members)+1}/8"
        new_guide_team_message = f"__**Run Guide**__\n{new_guide.mention}\n\n__**Runners**__\n{new_guide_member_names_str}\n-# {len(new_guide_members)+1}/8"
        
        # delete the old message
        message_id = teams[interaction.guild.id][current_guide.id]["message_id"]
        channel_id = teams[interaction.guild.id][current_guide.id]["channel_id"]
        
        # Delete the team message
        channel = self.client.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound:
            logger.error(f"Message not found: {message_id}", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        await interaction.followup.send(f"The run led by {current_guide.display_name} has been split into two runs.", ephemeral=False)

        logger.debug(f"Team message sent: {current_team_message}", {"user_id": current_guide.id, "username": current_guide.name, "display_name": current_guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})

        # Send the new message
        current_message = await interaction.channel.send(current_team_message, silent=True, allowed_mentions=discord.AllowedMentions.none())
        new_guide_message = await interaction.channel.send(new_guide_team_message, silent=True, allowed_mentions=discord.AllowedMentions.none())
        
        # Save team information
        teams[interaction.guild.id][current_guide.id] = {
            "message_id": current_message.id,
            "members": current_members,
            "channel_id": interaction.channel.id,  # Track the channel ID
        }
        teams[interaction.guild.id][new_guide.id] = {
            "message_id": new_guide_message.id,
            "members": new_guide_members,
            "channel_id": interaction.channel.id,  # Track the channel ID
        }

    @app_commands.command(name="closerun", description="Close the given leader's team.")
    @is_runner()
    async def closerun(self, interaction: discord.Interaction, guide: discord.Member = None) -> None:
        logger.command(interaction)
        await interaction.response.defer(ephemeral=True)  # Defer the response to get more time
        
        if guide is None:
            guide = interaction.user
            
        if interaction.guild.id not in teams:
            teams[interaction.guild.id] = {}
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
            
        if guide.id not in teams[interaction.guild.id]:
            logger.debug(f"{guide.display_name} does not lead a run at the moment.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
            await interaction.followup.send(f"{guide.display_name} does not lead a run at the moment.", ephemeral=True)
            return
        
        logger.debug(f"Closing the run with {guide.display_name}:{guide.id} as the runner.", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        message_id = teams[interaction.guild.id][guide.id]["message_id"]
        channel_id = teams[interaction.guild.id][guide.id]["channel_id"]
        
        # Delete the team message
        channel = self.client.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.errors.NotFound:
            logger.error(f"Message not found: {message_id}", {"user_id": guide.id, "username": guide.name, "display_name": guide.display_name, "guild_id": interaction.guild.id, "guild_name": interaction.guild.name, "channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        await interaction.followup.send(f"The run led by {guide.display_name} has been closed.", ephemeral=False)
        
        teams[interaction.guild.id].pop(guide.id)