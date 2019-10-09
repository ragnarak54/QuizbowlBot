import io

import asyncpg
import discord
from discord.ext import commands
from fuzzywuzzy import process

import config
import quizdb
import reading
import tournament


bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
startup_extensions = ["tournament"]
categories = ["mythology", "literature", "trash", "science", "history", "religion", "geography", "fine arts",
              "social science", "philosophy", "current events"]
aliases = {"lit": "literature", "myth": "mythology", "sci": "science", "geo": "geography", "art": "fine arts"}


@bot.event
async def on_ready():
    appinfo = await bot.application_info()
    bot.procUser = appinfo.owner
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_guild_join(guild):
    if bot.procUser not in list(guild.members):
        for channel in [x for x in guild.text_channels]:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send("Please first invite my creator, ragnarak54#9413 so he can"
                                   " help set the bot up for you!")
        await guild.leave()


@bot.command()
async def ping(ctx):
    await ctx.send("pong!")


@bot.command(name="bonus", aliases=['b'])
async def bonus_(ctx):
    await reading.bonus(bot, ctx)


@bot.command(name="question", aliases=['q', 'tossup', 't'])
async def question_(ctx, *, category=None):
    if category:
        results = get_matches(category, categories)
        if category in aliases:
            category = aliases[category]
        elif category not in results:
            if results[0][1] > 80:
                category = results[0][0]
            else:
                await ctx.send("Not sure what category you want. Try typing out the full name, or just do `?t` for "
                               "a random category")
                return
    await reading.tossup(bot, ctx.channel, category=category)


def get_matches(query, choices, limit=6):
    results = process.extract(query, choices, limit=limit)
    return results


@bot.command()
async def ms(ctx):
    await reading.tossup(bot, ctx.channel, ms=True)


@bot.command()
async def testformat(ctx):
    await ctx.send("test :bell: test")


def owner_check():
    def predicate(ctx):
        if ctx.author == bot.procUser:
            return True
        else:
            print("AHHH")
            return False

    return commands.check(predicate)


@bot.command(pass_context=True)
async def message_test(ctx):
    channel = ctx.message.channel
    embed = discord.Embed()
    embed.colour = discord.Colour.dark_blue()
    embed.set_footer(text="Updated stock for 10/22/2018")
    embed.description = "The new stock is out!"
    embed.set_image(url="attachment://res_img.png")
    with open('res_img.png', 'rb') as f:
        buffer = io.BytesIO(f.read())
    print("got here")
    data = await bot.http.send_file(channel.id, buffer, guild_id=channel.server.id,
                                    filename='res_img.png', embed=embed.to_dict())
    returned_message = bot.connection._create_message(channel=channel, **data)

bot.pool = bot.loop.run_until_complete(asyncpg.create_pool(config.psql))
bot.add_cog(quizdb.DB(bot))
bot.db = quizdb.DB(bot)
bot.add_cog(tournament.Tournament(bot))
bot.run(config.token)
