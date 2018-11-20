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
bonuslist = []
loaded = []
groups = []
teams = []
players = []


@bot.event
async def on_ready():
    appinfo = await bot.application_info()
    bot.procUser = appinfo.owner
    with open('geography.json', 'r') as file:
        decoded = json.loads(file.read())
    questions = []
    bonuses = []
    for dic in decoded["tossups"]:
        questions.append(question.Question(dic["question"], dic["answer"], dic["category"], dic["packet"],
                                           formatted_question=dic["formatted_question"],
                                           formatted_answer=dic["formatted_answer"]))
    print(len(questions))
    for dic in decoded["bonuses"]:
        bonuses.append(question.Bonus(dic["leadin"], dic["texts"], dic["answers"], dic["category"], dic["packet"],
                                      dic["formatted_texts"], dic["formatted_answers"]))
    questionlist.extend(questions)
    bonuslist.extend(bonuses)
    print(len(bonuses), "added")
    # with open('test2.json', 'r') as f:
    #     encoded_list = f.read()
    # decoded = json.loads(encoded_list)
    #
    # for dict in decoded:
    #     questionlist.append(question.Question(dict["question"], dict["answer"], None, dict["packet"]))
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
    while "</" not in question_obj.formatted_answer:
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
            sent_question_content = sent_question.content
            sent_question = await bot.edit_message(sent_question, sent_question_content + " :bell: ")
            await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
            answer = await bot.wait_for_message(timeout=10, author=msg.author)
            if answer is not None:
                matched = match(answer.content, question_obj.formatted_answer, "</" in question_obj.formatted_answer)
                if matched == "p":
                    await bot.say("prompt")
                    answer = await bot.wait_for_message(timeout=10, author=msg.author)
                    matched = match(answer.content, question_obj.formatted_answer, is_prompt=True)
                if matched == "y":
                    await bot.say("correct!")
                    correct = True
                    sent_question_content = sent_question.content
                    await bot.edit_message(sent_question, sent_question_content + " " + " ".join(question_arr[i * 5+5:]))
                    if playerlist:
                        team = tournament.get_team(msg.author, msg.author.server)
                        player = tournament.get_player(msg.author, msg.author.server)
                        team.score += 20
                        player.score += 20
                    break
                else:
                    await bot.say("incorrect!")
                    print("incorrect")
                    msg = None
                    sent_question = await bot.say(sent_question.content)
            else:
                await bot.say("Time's up!")
                sent_question = await bot.say(sent_question_content)
                await asyncio.sleep(1)
    wait_time = 7
    print(question_obj.formatted_answer)
    if not correct:

        while wait_time > 0:
            timer = time.time()
            msg = None
            if wait_time < 1:
                msg = await bot.wait_for_message(timeout=int(1), check=check)
            else:
                msg = await bot.wait_for_message(timeout=int(wait_time), check=check)
            wait_time -= (time.time() - timer)
            if wait_time < 0.5:
                break
            if msg is not None:
                await bot.edit_message(sent_question, sent_question.content + " :bell: ")
                await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                answer = None
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                if answer is not None:
                    matched = match(answer.content, question_obj.formatted_answer,
                                    "</" in question_obj.formatted_answer)
                    if matched == "p":
                        await bot.say("prompt")
                        answer = await bot.wait_for_message(timeout=10, author=msg.author)
                        matched = match(answer.content, question_obj.formatted_answer,
                                        "</" in question_obj.formatted_answer, is_prompt=True)
                    if matched == "y":
                        await bot.say("correct!")
                        correct = True
                        await bot.edit_message(sent_question, question_obj.question)
                        if playerlist:
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
            await print_answer(question_obj.formatted_answer, "</" in question_obj.formatted_answer)
            # await bot.say("The answer is {0}!".format(question_obj.answer))
    if correct and playerlist:
        await read_bonus(msg.author, team)

    neggers.clear()


async def read_bonus(author, team=None):
    print(author)
    print(author.name)

    bonus_obj = random.choice(bonuslist)
    question_arr = bonus_obj.leadin.split(" ")
    sent_question = await bot.say(" ".join(question_arr[:5]))
    await asyncio.sleep(1)
    for i in range(1, len(question_arr) // 5 + 1):
        sent_question_content = sent_question.content
        sent_question = await bot.edit_message(sent_question,
                                               sent_question_content + " " + " ".join(question_arr[i * 5:i * 5 + 5]))
        print(sent_question.content)
        await asyncio.sleep(1)

    # leadin done
    def check(message):
        if not team:
            return message.author == author
        return tournament.get_player(message.author, message.server) in team.members

    for j in range(0, 3):
        correct = False
        question_arr = bonus_obj.texts[j].split(" ")
        formatted = bonus_obj.formatted_answers[j]
        sent_question = await bot.say(" ".join(question_arr[:5]))
        await asyncio.sleep(1)
        for i in range(1, len(question_arr) // 5 + 1):
            sent_question_content = sent_question.content
            sent_question = await bot.edit_message(sent_question,
                                                   sent_question_content + " " + " ".join(question_arr[i * 5:i * 5 + 5]))
            await asyncio.sleep(1)

        msg = None
        msg = await bot.wait_for_message(timeout=10, check=check)
        if msg is not None:
            matched = match(msg.content, formatted,
                            "</" in formatted)
            if matched == "p":
                await bot.say("prompt")
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                matched = match(answer.content, formatted, "</" in formatted, is_prompt=True)
            if matched == "y":
                await bot.say("correct!")
                await print_answer(formatted, "</" in formatted)
                correct = True
                if team:
                    team = tournament.get_team(msg.author, msg.author.server)
                    player = tournament.get_player(msg.author, msg.author.server)
                    team.score += 10
                    player.score += 10
            else:
                await bot.say("incorrect!")
                print("incorrect")
        else:
            await bot.say("Time's up!")
            await asyncio.sleep(1)
        if not correct:
            await print_answer(bonus_obj.formatted_answers[j], "</" in formatted)
        await asyncio.sleep(1)


def match(given, answer, formatted, is_prompt=False):
    strong = []
    i = 0
    marker = 0
    tag = False
    prompt = False
    if formatted: # woohoo!
        answer = answer.replace("<u>", "").replace("</u>", "")
        while i < len(answer):
            if answer[i] == '<' and (answer[i+1:i+7] == "strong" or answer[i+1:i+3] == "em") and not tag:
                # found tag
                tag = True
                while answer[i] != '>':
                    i += 1
                i += 1
                marker = i
            # now in strong portion
            if answer[i] == '<' and (answer[i+1:i+8] == "/strong" or answer[i+1:i+4] == "/em")and tag:
                strong.append(answer[marker:i])
                tag = False
            i += 1

        for bold in strong:
            num_words = len(bold.split(" "))
            print("length", num_words)
            for i in range(0, len(given.split(" ")) - num_words + 1):
                phrase = " ".join(given.split(" ")[i:i+num_words])
                ratio = fuzz.ratio(phrase.lower(), bold.lower())
                print(bold, phrase, ratio)
                if ratio > 75:
                    return "y"
                if ratio > 55:
                    prompt = True
        if not is_prompt and prompt:
            return "p"
        else:
            return "n"
    else:
        answers = answer.replace("The", "").split(" ")
        givens = given.split(" ")
        prompt = False
        for word in answers:
            for w in givens:
                ratio = fuzz.ratio(w.lower(), word.lower())
                print(ratio)
                if ratio > 80:
                    return "y"
                if ratio > 55:
                    prompt = True
        if not is_prompt and prompt:
            return "p"
        return "n"


async def print_answer(answer: str, formatted):
    if not formatted:
        await bot.say(answer)
        return
    i = 0
    answer = answer.replace("<u>", "").replace("</u>", "")
    strongtag = False
    emtag = False
    printme = ""
    while i < len(answer):
        if answer[i] == '<' and answer[i + 1:i + 7] == "strong" and not strongtag:
            strongtag = True
            while answer[i] != '>':
                i += 1
            printme += "**"
        elif answer[i] == '<' and answer[i + 1:i + 3] == "em" and not emtag:
            emtag = True
            while answer[i] != '>':
                i += 1
            if printme[len(printme) - 2] == '*':
                printme += " *"
            else:
                printme += "*"
        elif answer[i] == '<' and answer[i + 1:i + 8] == "/strong" and strongtag:
            strongtag = False
            while answer[i] != '>':
                i += 1
            printme += "**"
        elif answer[i] == '<' and answer[i + 1:i + 4] == "/em" and emtag:
            emtag = False
            while answer[i] != '>':
                i += 1
            printme += "*"
        else:
            if answer[i] == '<':
                break
            printme += answer[i]
        i += 1
    await bot.say(printme)


@bot.command(pass_context=True, name="bonus")
async def bonus_(ctx):
    await read_bonus(ctx.message.author)


@bot.command()
async def load(category):
    if category in loaded:
        await bot.say(category + " already loaded")
        return
    with open(category + '.json', 'r') as file:
        decoded = json.loads(file.read())
    questions = []
    bonuses = []
    for dic in decoded["tossups"]:
        questions.append(question.Question(dic["question"], dic["answer"], dic["category"], dic["packet"],
                                           formatted_question=dic["formatted_question"],
                                           formatted_answer=dic["formatted_answer"]))
    print(len(questions))
    for dic in decoded["bonuses"]:
        bonuses.append(question.Bonus(dic["leadin"], dic["texts"], dic["answers"], dic["category"], dic["packet"],
                                      dic["formatted_texts"], dic["formatted_answers"]))
    questionlist.extend(questions)
    bonuslist.extend(bonuses)
    print(len(bonuses), "added")
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
                    matched = match(answer.content, question_obj.formatted_answer)
                    ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                    if matched == "y":
                        await bot.say("correct!")
                        correct = True
                        break
                    if matched == "p":
                        await bot.say("prompt")
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
