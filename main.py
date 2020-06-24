import io

import asyncio
import asyncpg
import discord
from discord.ext import commands
from fuzzywuzzy import process

import config
import quizdb
import reading
import resources
import tournament

bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
startup_extensions = ["tournament"]


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
    x = await bot.db.get_player_settings(ctx.author)
    print(x)
    print([f'{x}\ufe0f\u20e3' for x in range(1, 10)])
    await ctx.send("1\ufe0f\u20e3")


@bot.command(aliases=['diff'])
async def difficulty(ctx, *difficulties):
    if not difficulties:
        em = discord.Embed(title="Possible difficulties")
        diffs = [f"{x}: **{y}**\n" for x, y in zip(resources.difficulties_map.values(), resources.difficulties_map.keys())]
        em.description = "\u200b \u200b \u200b \u200b" + "\u200b \u200b \u200b \u200b".join(diffs)
        em.description += "\n usage: `?difficulty <integers separated by spaces>`\n" \
                          "Typing `?difficulty 1 2` will set your difficulty to only MS and easy HS."
        em.set_footer(text="use `?preferences` to edit your settings")
        await ctx.send(embed=em)
        return
    if difficulties[0] == 'all':
        try:
            await bot.db.set_difficulty(ctx.author, [1, 2, 3])
        except:
            await ctx.send("There was an error setting your difficulties.")
        return
    for diff in difficulties:
        if int(diff) not in [1, 2, 3, 4, 5, 6, 7, 8]:
            await ctx.send(f"{diff} isn't one of the possible difficulties! Make sure to input")
            return
    await bot.db.set_difficulty(ctx.author, [int(diff) for diff in difficulties])


@bot.command(aliases=["prefs"])
async def preferences(ctx):
    cats_int, diffs_int = await bot.db.get_player_settings(ctx.author)
    current_cats = dict(zip())
    cats_str = 'all' if not cats_int else ', '.join([resources.categories_map[int(x)] for x in cats_int])
    diffs_str = 'all HS' if not diffs_int else ', '.join([resources.difficulties_map[x] for x in diffs_int])
    em = discord.Embed(title="Player preferences menu")
    em.description = f"Current preferences for **{ctx.author.display_name}**:\n" \
        f"\u200b \u200b \u200b \u200bPossible categories: **{cats_str}**\n" \
        f"\u200b \u200b \u200b \u200bPossible difficulties: **{diffs_str}**\n\n" \
        f"Click the reaction to edit your personal settings"
    em.set_footer(text="These settings are global")
    msg = await ctx.send(embed=em)
    await msg.add_reaction("\U0001f4dd")

    def check(reaction: discord.Reaction, user):
        return user == ctx.author and str(reaction.emoji) == "\U0001f4dd" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", check=check, timeout=30)
    except asyncio.TimeoutError:
        return
    x = '\u274c'
    check_mark = '\u2705'
    poss_cats = ''
    for i in range(len(resources.categories)):
        poss_cats += f"\u200b \u200b \u200b \u200b{resources.emojis[i]} {resources.categories[i]} " \
            f"{check_mark if resources.categories[i] in cats_str else x}\n"
    em = discord.Embed(title="Change possible categories")
    em.description = f"Current categories for **{ctx.author.display_name}:**\n" \
        f"{poss_cats}\nClicking on a category's reaction will activate or deactivate it. Press the check mark to " \
        f"save your changes! Press the 'next' reaction to edit difficulties"

    msg = await ctx.send(embed=em)
    for i in range(len(resources.categories)):
        await msg.add_reaction(resources.emojis[i])
    await msg.add_reaction("\u2705")
    await msg.add_reaction("\u25b6\ufe0f")

    def check2(reaction, user):
        print(user == ctx.author and str(reaction.emoji) in resources.emojis + ["\u2705", "\u25b6\ufe0f"])
        return user == ctx.author and str(reaction.emoji) in resources.emojis + ["\u2705", "\u25b6\ufe0f"]

    dic = dict(zip(resources.emojis, resources.categories))
    try:
        reaction, user = await bot.wait_for("reaction_add", check=check2, timeout=30)
    except asyncio.TimeoutError:
        return
    while str(reaction.emoji) != "\u25b6\ufe0f":
        await msg.remove_reaction(reaction, user)
        index = resources.emojis.index(str(reaction.emoji))
        poss_cats = ''
        for i in range(len(resources.categories)):
            if i == index:
                poss_cats += f"\u200b \u200b \u200b \u200b{resources.emojis[i]} {resources.categories[i]} " \
                    f"{check_mark if resources.categories[i] not in cats_str else x}\n"
            else:
                poss_cats += f"\u200b \u200b \u200b \u200b{resources.emojis[i]} {resources.categories[i]} " \
                    f"{check_mark if resources.categories[i] in cats_str else x}\n"
        print('gt here')
        em.description = f"Current categories for **{ctx.author.display_name}:**\n" \
            f"{poss_cats}\nClicking on a category's reaction will activate or deactivate it. Press the check mark to " \
            f"save your changes! Press the 'next' reaction to edit difficulties"
        await msg.edit(embed=em)
        try:
            reaction, user = await bot.wait_for("reaction_add", check=check2, timeout=30)
        except asyncio.TimeoutError:
            break
        print('got here')


@bot.command(name="bonus", aliases=['b'])
async def bonus_(ctx):
    await reading.bonus(bot, ctx)


@bot.command(name="question", aliases=['q', 'tossup', 't'])
async def question_(ctx, *, category=None):
    if category:
        try:
            await reading.tossup(bot, ctx, q_id=int(category))
            return
        except ValueError:
            results = get_matches(category, resources.categories)
            if category in resources.aliases:
                category = resources.aliases[category]
            elif category not in results:
                if results[0][1] > 80:
                    category = results[0][0]
                else:
                    await ctx.send("Not sure what category you want. Try typing out the full name, or just do `?t` for "
                                   "a random category")
                    return
        category = resources.categories_map_inv[category]
    await reading.tossup(bot, ctx, category=category)


@bot.command()
async def tryout(ctx):
    questions = [77859,77729,77796,155528,155571,155459,122263,113517,155443,155450,69789,77624,155662,155596,155632,
                 114597,69687,113465,114376,122370,113501,70009,114414,77807,69736,113306,77778,77740,77603,155584,
                 113546,77821,69958,70003]

    def check(message):
        return message.author == ctx.author and message.content == "n" or message.content == "quit"
    i = 1
    for question in questions:
        await ctx.send(f"question #{i} of 34:")
        await reading.tossup(bot, ctx, q_id=question)
        if i == 34:
            break
        i += 1
        msg = await bot.wait_for("message", check=check)
        if msg.content == "quit":
            break
    await ctx.send("Thanks for trying out! We'll get back to you with your results as soon as possible.")


def get_matches(query, choices, limit=6):
    results = process.extract(query, choices, limit=limit)
    return results


@bot.command()
async def ms(ctx):
    await reading.tossup(bot, ctx, ms=True)


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
