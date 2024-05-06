import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
)

import random
import os

import discord
from discord.ext import commands
import emoji

from chance import ChanceCog
from mocking import MockingCog
from channels.cog import ChannelsCog
from games.cah.cog import CardsAgainstHumanityCog
from games.ridethebus.cog import RideTheBusCog
from rp import RoleplayCog

COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "?")

logger = logging.getLogger(__name__)

# Set discord status
activity = discord.Game(
    name=emoji.emojize(":partying_face: Party Games :party_popper:")
)
# Set discord permissions
intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    reactions=True,
    voice_states=True,
)
# Configure discord bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, activity=activity)


@bot.event
async def on_ready():
    if not hasattr(bot, "appinfo"):
        bot.appinfo: discord.AppInfo = await bot.application_info()
    logger.info("We have logged in as {0.user}".format(bot))


@bot.command(brief="Ping the bot [DEBUG]")
async def ping(ctx: commands.Context):
    logger.info("got ping")
    await ctx.send("pong")


@bot.command(brief="Report a problem with the bot")
async def complain(ctx: commands.Context, *args):
    owner: discord.User = bot.appinfo.owner
    embed = discord.Embed(title="COMPLAINT", color=0xFF0000, description=" ".join(args))
    embed.set_author(
        name=ctx.author.name,
        icon_url=ctx.author.avatar_url,
    )
    if ctx.guild:
        embed.set_footer(text=f"{ctx.guild.name}:{ctx.channel.name}")
    await ctx.author.send(embed=embed)
    await owner.send(embed=embed)


@bot.command(hidden=True)
@commands.is_owner()
async def say(ctx: commands.Context, channel: discord.TextChannel, *msg):
    if ctx.message.channel.type == discord.ChannelType.text:
        await ctx.message.delete()
    await channel.send(" ".join(msg))


@say.error
async def say_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("I couldn't resolve that channel.")


bot.add_cog(ChanceCog(bot))
bot.add_cog(ChannelsCog(bot))
bot.add_cog(MockingCog(bot))
bot.add_cog(CardsAgainstHumanityCog(bot))
bot.add_cog(RideTheBusCog(bot))
bot.add_cog(RoleplayCog(bot))

# RELEASE THE KRAKEN
bot.run(os.environ["DISCORD_TOKEN"])
