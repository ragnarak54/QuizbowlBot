import discord
from discord.ext import commands
import packet_handling
import random
from fuzzywuzzy import fuzz
import asyncio

bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
questionlist = packet_handling.get_questions()

@bot.event
async def on_ready():

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def ping():
    await bot.say("pong!")


@bot.command(pass_context=True)
async def question(ctx):
    correct = False
    user = ctx.message.author
    while not correct:
        question_obj = random.choice(questionlist)
        question_arr = question_obj.question.split(" ")
        sent_question = await bot.say(" ".join(question_arr[:5]))
        await asyncio.sleep(1)
        for i in range(1, question_arr.__len__() // 5 + 1):
            sent_question_content = sent_question.content
            sent_question = await bot.edit_message(sent_question, sent_question_content + " " + " ".join(question_arr[i*5:i*5+5]))
            print(sent_question.content)
            await asyncio.sleep(1)

        msg = await bot.wait_for_message(author=user)
        print(question_obj.question)
        ratio = fuzz.ratio(msg.content.lower(), question_obj.answer.lower())
        if ratio > 80:
            await bot.say("correct!")
            print("correct! ratio: " + str(ratio))
            correct = True
        else:
            await bot.say("incorrect :(\nIt was " + question_obj.answer + "!")
            print("incorrect")
        print(question_obj.answer)
        print(question_obj.packet)


bot.run('NDc1MTY3NTk5MjE1Mzc4NDk0.DkbLrw.fp-6BdSSGQmfR1vXNd43V0K8Fcg')
