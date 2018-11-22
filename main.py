import discord
from discord.ext import commands
import config
import io
import reading

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


@bot.command()
async def ping():
    await bot.say("pong!")
    

@bot.command(pass_context=True, name="bonus", aliases=['b'])
async def bonus_(ctx):
    await reading.read_bonus(bot, ctx.message.author)


@bot.command(pass_context=True, name="question", aliases=['q'])
async def question_(ctx, num=1):
    await reading.read_question(bot)
    return


@bot.command()
async def testformat():
    await bot.say("test :bell: test")


def owner_check():
    def predicate(ctx):
        if ctx.message.author == bot.procUser:
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


@bot.command()
@owner_check()
async def ping_boss():
    await bot.say("<@!208229380575592448>")

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    bot.run(config.token)
