import discord
from discord.ext import commands
import random
from fuzzywuzzy import fuzz
import asyncio
import config
import time
import json
import question
import io
import tournament

bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
startup_extensions = ["tournament"]
questionlist = []
groups = []
teams = []
players = []


@bot.event
async def on_ready():
    appinfo = await bot.application_info()
    bot.procUser = appinfo.owner
    with open('test2.json', 'r') as f:
        encoded_list = f.read()
    decoded = json.loads(encoded_list)

    for dict in decoded:
        questionlist.append(question.Question(dict["question"], dict["answer"], None, dict["packet"]))
    print(len(questionlist))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def ping():
    await bot.say("pong!")
    

async def read_question(bonus=False, playerlist=None):
    # print([str(player) for player in playerlist])
    correct = False
    skip = False
    neggers = []
    question_obj = random.choice(questionlist)
    question_arr = question_obj.question.split(" ")
    sent_question = await bot.say(" ".join(question_arr[:5]))
    await asyncio.sleep(1)
    for i in range(1, question_arr.__len__() // 5 + 1):
        sent_question_content = sent_question.content
        sent_question = await bot.edit_message(sent_question,
                                               sent_question_content + " " + " ".join(question_arr[i * 5:i * 5 + 5]))
        print(sent_question.content)

        def check(message):
            if not playerlist:
                return message.author not in neggers and "buzz" in message.content
            return tournament.get_player(message.author, message.server) in playerlist and message.author not in neggers and "buzz" in message.content

        msg = None
        msg = await bot.wait_for_message(timeout=1, check=check)
        if msg is not None:
            await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
            answer = await bot.wait_for_message(timeout=10, author=msg.author)
            if answer is not None:
                ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                if ratio > 75:
                    await bot.say("correct!")
                    print("correct! ratio: " + str(ratio))
                    correct = True
                    await bot.edit_message(sent_question, question_obj.question)
                    team = tournament.get_team(msg.author, msg.author.server)
                    player = tournament.get_player(msg.author, msg.author.server)
                    team.score += 20
                    player.score += 20
                    break
                else:
                    await bot.say("incorrect!")
                    print("incorrect")
                    msg = None
                    sent_question = await bot.say(sent_question_content)
            else:
                await bot.say("Time's up!")
                await asyncio.sleep(1)
    wait_time = 7
    if not correct:

        while wait_time > 0:
            timer = time.time()
            print("waiting for " + str(wait_time))
            msg = None
            msg = await bot.wait_for_message(timeout=int(wait_time), check=check)
            wait_time -= (time.time() - timer)  # new wait time = old time - (time elapsed waiting for buzz =
            if wait_time < 0.5:
                break
            if msg is not None:
                await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                answer = None
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                if answer is not None:
                    ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                    if ratio > 75:
                        await bot.say("correct!")
                        print("correct! ratio: " + str(ratio))
                        correct = True
                        team = tournament.get_team(msg.author, msg.author.server)
                        player = tournament.get_player(msg.author, msg.author.server)
                        team.score += 20
                        player.score += 20
                        break
                    else:
                        await bot.say("incorrect!")
                        print("incorrect")
                else:
                    await bot.say("Time's up!")
                    await asyncio.sleep(1)

        if not correct:
            await bot.say("The answer is {0}!".format(question_obj.answer))

    neggers.clear()


@bot.command()
async def load(category):
    with open(category + '.json', 'r') as file:
        decoded = json.loads(file.read())
    questions = []
    for dic in decoded:
        questions.append(question.Question(dic["question"], dic["answer"], dic["category"], dic["packet"],
                                           formatted_question=dic["formatted_question"],
                                           formatted_answer=dic["formatted_answer"]))
    print(len(questions))
    questionlist.extend(questions)
    await bot.say(category + " (" + str(len(questions)) + " questions) loaded. New total of " +
                  str(len(questionlist)) + " questions.")


@bot.command(pass_context=True, name="question", aliases=['q'])
async def question_(ctx, num=1):
    if not questionlist:
        await bot.say("No questions loaded")
        return
    await read_question()
    return
    correct = False
    skip = False
    user = ctx.message.author
    wrong_buzzers = []
    for j in range(0, num):

        question_obj = random.choice(questionlist)

        # reading_task = bot.loop.create_task(read_question(question_obj))

        # loop.run_until_complete(asyncio.ensure_future(read_question(question_obj), loop=loop))
        question_arr = question_obj.question.split(" ")
        sent_question = await bot.say(" ".join(question_arr[:5]))
        await asyncio.sleep(1)
        for i in range(1, question_arr.__len__() // 5 + 1):
            sent_question_content = sent_question.content
            sent_question = await bot.edit_message(sent_question, sent_question_content + " " + " ".join(question_arr[i*5:i*5+5]))
            print(sent_question.content)

            def check(message):
                return message.author not in wrong_buzzers and "buzz" in message.content
            msg = None
            msg = await bot.wait_for_message(timeout=1)
            if msg is not None:
                if "buzz" in msg.content:
                    await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                    answer = await bot.wait_for_message(timeout=10, author=msg.author)
                    ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                    if ratio > 80:
                        await bot.say("correct!")
                        print("correct! ratio: " + str(ratio))
                        correct = True
                        msg = None
                        break
                    else:
                        await bot.say("incorrect!")
                        if answer.author not in wrong_buzzers:
                            wrong_buzzers.append(answer.author)
                        print("incorrect")
                        msg = None
                        sent_question = await bot.say(sent_question_content + " " + " ".join(question_arr[i*5:i*5+5]))
                elif "skip" in msg.content:
                    skip = True
                    print("skip!")
                    break

        if not skip:
            msg = await bot.wait_for_message(timeout=10, check=check)
            if msg is not None:
                await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                if ratio > 80:
                    await bot.say("correct!")
                    print("correct! ratio: " + str(ratio))
                    correct = True
                else:
                    await bot.say("incorrect!")
                    print("incorrect")
            if not correct:
                await bot.say("The answer is {0}!".format(question_obj.answer))
            msg = None
            msg = await bot.wait_for_message(timeout=20, content="next")
            if msg is None:
                return

        wrong_buzzers.clear()
        print(question_obj.answer)
        print(question_obj.packet)


@bot.command()
async def testformat():
    await bot.say("**bold text?**")


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
